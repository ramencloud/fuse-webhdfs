import argparse
from dataclasses import dataclass
from sys import argv


@dataclass
class WebHDFSConfig:
    hdfs_host: str
    hdfs_baseurl: str

    hdfs_port: str = '30070'
    hdfs_user_name: str = None

    proxy_host: str = None
    proxy_port: str = '1080'

    mountpoint: str = None
    logfile: str = None


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


DEFAULT_HDFS_PORT = '30070'
DEFAULT_PROXY_PORT = '1080'


def commandline_parser():
    parser = argparse.ArgumentParser()

    parser.add_argument('hdfs_host:hdfs_port', action=Split,
                        default=f':{DEFAULT_HDFS_PORT}',
                        metavar='<server[:port]>',
                        help=f'If the port number is not specified, '
                             f'it is assumed to be {DEFAULT_HDFS_PORT}')

    parser.add_argument('--user.name', dest='hdfs_user_name', help='HDFS user name')
    parser.add_argument('--logfile', help='Optional file to log all fs operations')

    parser.add_argument('--socks5h', action=Split, dest='proxy_host:proxy_port', default=f':{DEFAULT_PROXY_PORT}',
                        metavar='<host[:port]>',
                        help=f'If the port number is not specified, '
                             f'it is assumed to be {DEFAULT_PROXY_PORT}')

    return parser


def configure(parser=commandline_parser()):
    args = parser.parse_args(argv[1:])

    args.hdfs_baseurl = f"http://{args.hdfs_host}:{args.hdfs_port}/webhdfs/v1/"
    config = WebHDFSConfig(**args.__dict__)
    return config


if __name__ == '__main__':
    config = configure()
    print('Base URL: ', config.hdfs_baseurl)
    if config.proxy_host:
        print('Proxy: ', f'{config.proxy_host}:{config.proxy_port}')
