all: build

build:
	make -C src
	cp src/jedi_increment bin/

run: build
	make -C bin

clean:
	make -C src clean
