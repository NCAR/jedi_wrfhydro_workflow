FC=mpif90
SRC=$(wildcard *.f90)
OBJS=$(patsubst %.f90, %.o, $(SRC))
EXE=jedi_increment
ifdef NETCDF
	netcdf=	-I$(NETCDF)/include -L$(NETCDF)/lib -lnetcdff
endif
FFLAGS=-O3 $(netcdf)

%.o: %.f90
	$(FC) -c $(FFLAGS) $<

all: build

build: $(OBJS)
	$(FC) $(OBJS) $(FFLAGS) -o $(EXE)

jedi_snow_incr.o: jedi_disag_mod.o input_var_names.o

clean:
	rm -f $(OBJS) *.mod $(EXE) *~
