import argparse
import configparser
from dataclasses import dataclass
from distutils.util import strtobool
from sys import argv
from os import environ, path

@dataclass
class WebHDFSConfig:
    hdfs_host: str
    hdfs_baseurl: str

    use_apache_knox: bool

    hdfs_port: str = '30070'
    hdfs_username: str = None
    hdfs_password: str = None
    hdfs_cert: str = None

    proxy_host: str = None
    proxy_port: str = '1080'

    mountpoint: str = None


class Split(argparse.Action):
    def __init__(self, option_strings, dest, **kwargs):
        self.splits = dest.split(':')
        super().__init__(option_strings, argparse.SUPPRESS, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        split_values = values.split(':')
        self.defaults = self.default.split(':') if self.default else []
        values = split_values + self.defaults[len(split_values):]
        for (dest, value) in zip(self.splits, values):
            setattr(namespace, dest, value)


def commandline_parser():
    DEFAULT_HDFS_PORT = '30070'
    DEFAULT_PROXY_PORT = '1080'

    cfg = configparser.ConfigParser()
    try:
        with open(path.join(environ['HOME'], '.config', 'webhdfs.ini')) as configfile:
            cfg.read_file(configfile)
    except IOError:
            pass

    parser = argparse.ArgumentParser()

    parser.add_argument('hdfs_host:hdfs_port', action=Split,
                        default=f'{cfg.defaults().get("hdfs_host", "")}:{DEFAULT_HDFS_PORT}',
                        metavar='<server[:port]>',
                        nargs='?' if 'hdfs_host' in cfg.defaults() else None,
                        help=f'If the port number is not specified, '
                             f'it is assumed to be {DEFAULT_HDFS_PORT}')

    parser.add_argument('--hdfs-user', action=Split, dest='hdfs_username:hdfs_password', metavar='<user:password>')

    parser.add_argument('--hdfs-cacert', action='store', dest='hdfs_cert')

    parser.add_argument('--knox', action='store_true', dest='use_apache_knox',
                        help='Hadoop is configured with Apache Knox Gateway. '
                             'Ignores port argument.')

    parser.add_argument('--socks5h', action=Split, dest='proxy_host:proxy_port', default=f':{DEFAULT_PROXY_PORT}',
                        metavar='<host[:port]>',
                        help=f'If the port number is not specified, '
                             f'it is assumed to be {DEFAULT_PROXY_PORT}')

    defaults = cfg.defaults()
    defaults['use_apache_knox'] = strtobool(defaults.get('use_apache_knox', 'No'))
    parser.set_defaults(**defaults)
    return parser


def configure(parser=commandline_parser()):
    args = parser.parse_args(argv[1:])

    hdfs_host = args.__dict__.pop('hdfs_host')
    hdfs_port = args.hdfs_port
    use_apache_knox = args.use_apache_knox

    args.hdfs_baseurl = f"https://{hdfs_host}:8443/gateway/webhdfs/webhdfs/v1/" \
        if use_apache_knox \
        else f"http://{hdfs_host}:{hdfs_port}/webhdfs/v1/"
    config = WebHDFSConfig(hdfs_host, **args.__dict__)
    return config


if __name__ == '__main__':
    config = configure()
    print('Base URL: ', config.hdfs_baseurl)
    if config.proxy_host:
        print('Proxy: ', f'{config.proxy_host}:{config.proxy_port}')
    if config.hdfs_username:
        print('Auth: ', f'{config.hdfs_username}:{config.hdfs_password}')
