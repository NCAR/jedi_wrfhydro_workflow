restart=RESTART.2017010100_DOMAIN1
increment=RESTART.2017010100_DOMAIN1_SNEQV_plus100

all: build

.PHONY: build
build:
	make -C ../ build

cp:
	cp $(restart).orig $(restart)

run: build cp
	./jedi_increment $(restart) $(increment)

comp:
	nccmp -dfS  $(restart) $(restart).orig

clean:
	rm jedi_increment
	make -C ../ clean
