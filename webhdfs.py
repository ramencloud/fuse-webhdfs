#!/usr/bin/env python3

import os
import getpass
import pwd
import grp
from config.webhdfs import configure
from netrc import netrc, NetrcParseError
from pywebhdfs.webhdfs import PyWebHdfsClient
from stat import S_IFDIR, S_IFLNK, S_IFREG
from time import time
from distutils.util import strtobool
import datetime
import configparser

cfg = configparser.ConfigParser()
def write_default_config():
    config = configure()
    if not os.path.exists(os.environ['HOME'] + '/.config'):
        os.makedirs(os.environ['HOME'] + '/.config')
    webhdfs_host = input(f"WebHDFS hostname [{config.hdfs_host}]: ") or config.hdfs_host
    cfg.set('DEFAULT', 'HDFS_HOST', webhdfs_host)

    configure_knox = input(f"Configure With Apache Knox Gateway (Yes/No)? "
                           f"[{config.use_apache_knox and 'Yes' or 'No'}]: ") or (config.use_apache_knox
                                                                                  and 'Yes'
                                                                                  or 'No')
    cfg.set('DEFAULT', 'USE_APACHE_KNOX', configure_knox)

    if strtobool(configure_knox):
        webhdfs_username = input("HDFS username: ")
        cfg.set('DEFAULT', 'HDFS_USERNAME', webhdfs_username)
        webhdfs_password = getpass.getpass(prompt="HDFS password: ")
        cfg.set('DEFAULT', 'HDFS_PASSWORD', webhdfs_password)
        webhdfs_cert = input(f"HDFS web server certificate path [{config.hdfs_cert}: ") or config.hdfs_cert
        cfg.set('DEFAULT', 'HDFS_CERT', webhdfs_cert)
    else:
        webhdfs_port = input(f"WebHDFS port [{config.hdfs_port}]: ") or config.hdfs_port
        cfg.set('DEFAULT', 'HDFS_PORT', webhdfs_port)

    with open(os.environ['HOME'] + '/.config/webhdfs.ini', 'w') as configfile:
        cfg.write(configfile)

if not os.path.exists(os.environ['HOME'] + '/.config/webhdfs.ini'):
    write_default_config()

cfg.read(os.environ['HOME'] + '/.config/webhdfs.ini')

def get_auth(config):
    username = password = None
    try:
        username, account, password = netrc().authenticators(cfg['DEFAULT']['HDFS_HOST'])
    except (FileNotFoundError, NetrcParseError, TypeError):
        pass
    if not username:
        username = cfg['DEFAULT'].get('HDFS_USERNAME', "")
    if not password:
        password = cfg['DEFAULT'].get('HDFS_PASSWORD', "")
    if 'HDFS_USERNAME' in os.environ:
        username = os.environ['HDFS_USERNAME']
    else:
        if not username:
            username = input("HDFS Username: ")
    if 'HDFS_PASSWORD' in os.environ:
        password = os.environ['HDFS_PASSWORD']
    else:
        if not password:
            password = getpass.getpass(prompt="HDFS Password: ")
    return (username.lower(), password)

uid_cache = dict()
def owner_to_uid(owner):
    if owner in uid_cache:
        return uid_cache[owner]
    try:
        uid_cache[owner] = pwd.getpwnam(owner)[2]
        return pwd.getpwnam(owner)[2]
    except KeyError:
        res = pwd.getpwnam('nobody')[2] or 0
        uid_cache[owner] = res
        return res

gid_cache = dict()
def group_to_gid(group):
    if group in gid_cache:
        return gid_cache[group]
    for g in [group, 'nogroup', 'nobody']:
        try:
            gid_cache[group] = grp.getgrnam(g)[2]
            return grp.getgrnam(g)[2]
        except KeyError:
            pass
    gid_cache[group] = 0
    return 0

def webhdfs_connect(config):
    request_extra_opts = {}
    if config.use_apache_knox:
        request_extra_opts['verify'] = config.hdfs_cert
        request_extra_opts['auth'] = get_auth(config)
    if config.proxy_host:
        request_extra_opts['proxies'] ={'http': f'socks5h://{config.proxy_host}:{config.proxy_port}',
                                        'https': f'socks5h://{config.proxy_host}:{config.proxy_port}'}
    webhdfs = PyWebHdfsClient(base_uri_pattern=config.hdfs_baseurl,
                              request_extra_opts=request_extra_opts)
    return webhdfs

def webhdfs_entry_to_dict(s):
    mode = int(s['permission'], 8)
    if s['type'] == 'DIRECTORY':
        mode |= S_IFDIR
    else:
        mode |= S_IFREG
    mtime = s['modificationTime'] / 1000
    atime = s['accessTime'] / 1000
    blksize = max(s['blockSize'], 1024*1024)
    sd = dict(name=s['pathSuffix'],
              st_mode=mode,
              st_ctime=mtime,
              st_mtime=mtime,
              st_atime=atime,
              st_nlink=s['childrenNum'] or 1,
              st_blocks=s['length'] // blksize,
              st_size=s['length'],
              st_creator = s['owner'],
              st_uid=owner_to_uid(s['owner']),
              st_gid=group_to_gid(s['group']),
              st_blksize=blksize)
    return sd

if __name__ == '__main__':
    webhdfs = webhdfs_connect(configure())
    now = time()
    for s in webhdfs.list_dir('/')["FileStatuses"]["FileStatus"]:
        sd = webhdfs_entry_to_dict(s)
        print("{:16}\t{:6}\t{:16}\t{:16}\t{}\t{:9}\t{}"
              .format(sd['st_mode'], sd['st_nlink'], sd['st_uid'],
                      sd['st_gid'], sd['st_blocks'],
                      datetime.datetime.fromtimestamp(sd['st_mtime'] / 1000).strftime('%Y-%m-%d %H:%M'),
                      sd['name']))
