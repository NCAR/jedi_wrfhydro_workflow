all: build

.PHONY: build
build:
	make -C src
	cp src/jedi_increment bin/

clean:
	make -C src clean
	make -C bin clean
