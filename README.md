# Description

Mount WebHDFS on your local Linux or Mac file system

After this, you can access the WebHDFS file system as if was a local directory - with regular Unix file operations.

# Installation

First dependency is fuse, you can install it on Ubuntu with:
```
sudo apt-get install fuse
```

or on RedHat with:
```
sudo yum install fuse
```

To install mount-webhdfs binary run:
```
make
sudo make install
```

# General Usage

```
mkdir -p ~/fuse-webhdfs
mount-webhdfs <server[:port]> fuse-webhdfs
```

You will be able to list files, read them, etc.


# Proxy connection

`mount-webhdfs` accepts `--socks5h` argument if you are not in the same network as your WebHDFS installation.

You have to setup the proxy yourself, you can do it using `ssh`:
```
ssh -D 1080 -f -N username@server
> username@server's password:
mount-webhdfs <server[:port]> --socks5h localhost
```

# Logging

Pass `--logfile <logfilename>` to enable logging fs operations.
