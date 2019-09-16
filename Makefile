.ONESHELL:
build/mount-webhdfs: build
	docker build $(CURDIR) --tag fuse-webhdfs;
	CONTAINER_ID=$$(docker create fuse-webhdfs);
	trap "docker rm -v $$CONTAINER_ID" EXIT;
	docker cp "$$CONTAINER_ID":/fuse-webhdfs/dist/mount-webhdfs $(CURDIR)/build/mount-webhdfs;

build:
	mkdir $(CURDIR)/build

install: mount-webhdfs
	cp $(CURDIR)/build/mount-webhdfs /usr/local/bin/mount-webhdfs

clean:
	rm -rf $(CURDIR)/build;
