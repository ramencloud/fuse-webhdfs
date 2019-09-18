#!/usr/bin/env python3

import pwd
import grp
from config.webhdfs import configure
from pywebhdfs.webhdfs import PyWebHdfsClient
from stat import S_IFDIR, S_IFLNK, S_IFREG
from time import time
import datetime

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
    if config.proxy_host:
        request_extra_opts['proxies'] ={'http': f'socks5h://{config.proxy_host}:{config.proxy_port}',
                                        'https': f'socks5h://{config.proxy_host}:{config.proxy_port}'}
    if config.hdfs_user_name:
        request_extra_opts['params'] ={'user.name': config.hdfs_user_name}
    client = PyWebHdfsClient(base_uri_pattern=config.hdfs_baseurl,
                             request_extra_opts=request_extra_opts)
    return client

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
