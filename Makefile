all: build

build:
	make -C src

run: build
	make -C bin
