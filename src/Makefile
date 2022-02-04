FC=mpif90
SRC=$(wildcard *.f90)
OBJS=$(patsubst %.f90, %.o, $(SRC))
EXE=jedi_increment
FFLAGS=-I$(NETCDF_INCLUDES) -L$(NETCDF_LIBRARIES) -lnetcdff -O3


%.o: %.f90
	$(FC) -c $(FFLAGS) $< #-o $@

all: build

build: $(OBJS)
	$(FC) $(OBJS) $(FFLAGS) -o $(EXE)

jedi_snow_incr.o: jedi_disag_mod.o

install:
	-cp -p $(CMD) ../exec/.
clean:
	-rm -f $(OBJS) *.mod $(EXE) *~
