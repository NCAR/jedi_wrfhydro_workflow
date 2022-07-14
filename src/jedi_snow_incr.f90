program jedi_snow_incr
  use netcdf
  use mpi
  use jedi_disag_module, only : jedi_type, updateAllLayers
  implicit none

  type(jedi_type) :: jedi_state
  integer :: we_res, sn_res, len_land_vec
  ! index to map between tile and vector space
  integer, allocatable :: tile2vector(:,:)
  double precision, allocatable :: increment(:,:)
  integer :: restart_file, increment_file
  integer :: ierr, nprocs, myrank, lunit
  integer :: snow_layers, soil_layers, sosn_layers !sosn=soil+snow layers
  logical :: file_exists

  ! namelist /jedi_snow/ date_str, hour_str, we_res ,sn_res

  call MPI_Init(ierr)
  call MPI_Comm_size(MPI_COMM_WORLD, nprocs, ierr)
  call MPI_Comm_rank(MPI_COMM_WORLD, myrank, ierr)

  call open_data_files(restart_file, increment_file, we_res, sn_res)

  ! The mapping call is old code, don't need it with regular indexing
  ! GET MAPPING INDEX (see subroutine comments re: source of land/sea mask)
  ! call get_fv3_mapping(myrank, date_str, hour_str, res, len_land_vec, tile2vector)

  ! SET-UP THE JEDI STATE AND INCREMENT
  snow_layers = 3
  soil_layers = 4
  sosn_layers = 7
  allocate(jedi_state%swe(we_res, sn_res))
  allocate(jedi_state%snow_depth         (we_res, sn_res))
  allocate(jedi_state%active_snow_layers (we_res, sn_res))
  allocate(jedi_state%swe_previous       (we_res, sn_res))
  allocate(jedi_state%snow_soil_interface(we_res, sosn_layers, sn_res))
  allocate(jedi_state%temperature_snow   (we_res, snow_layers, sn_res))
  allocate(jedi_state%snow_ice_layer     (we_res, snow_layers, sn_res))
  allocate(jedi_state%snow_liq_layer     (we_res, snow_layers, sn_res))
  allocate(jedi_state%temperature_soil   (we_res, sn_res))
  allocate(increment(we_res, sn_res))

  call read_wrf_hydro_restart(restart_file, we_res, sn_res, jedi_state )
  call read_wrf_hydro_increment(increment_file, we_res, sn_res, increment)

  jedi_state%snow_depth = jedi_state%snow_depth * 1000

  increment = (increment * 1000) - jedi_state%snow_depth

  ! ADJUST THE RESTART
  print *, "Updating Data"
  call updateAllLayers(we_res, sn_res, increment, jedi_state)

  jedi_state%snow_depth = jedi_state%snow_depth / 1000

  ! WRITE OUT ADJUSTED RESTART
  print *, "Writing WRF-Hydro Restart Data"
  call write_wrf_hydro_restart(restart_file, we_res, sn_res, jedi_state)

  ! CLOSE RESTART FILE
  ierr = nf90_close(restart_file)
  call netcdf_err(ierr, 'closing restart file')

  call MPI_Finalize(ierr)

contains

  subroutine open_data_files( restart_file, increment_file, we_res, sn_res )
    implicit none
    integer, intent(out) :: restart_file, increment_file, we_res, sn_res
    integer :: restart_we, restart_sn, incr_we, incr_sn
    integer :: ierr, mpierr

    call open_command_line_file(restart_file, 1)
    call open_command_line_file(increment_file, 2)

    call get_dimensions(restart_file, restart_we, restart_sn)
    call get_dimensions(increment_file, incr_we, incr_sn)

    if ( restart_we /= incr_we .or. restart_sn /= incr_sn) then
       print*, 'fatal error: dimensions for restart and increment file do not &
            &match'
       call MPI_Abort(MPI_COMM_WORLD, ierr, mpierr)
    endif
    we_res = restart_we
    sn_res = restart_sn
  end subroutine open_data_files

  subroutine open_command_line_file(f, pos)
    integer, intent(out) :: f
    integer, intent(in) :: pos
    character(len=1028) :: file
    character(len=10) :: file_type
    logical :: file_exists
    integer :: ierr

    if (pos == 1) then
       file_type = "restart"
    else if (pos == 2) then
       file_type = "increment"
    end if

    call get_command_argument(pos, file)
    inquire(file=trim(file), exist=file_exists)

    if (.not. file_exists) then
       print *, trim(file), 'does not exist, exiting'
       call MPI_Abort(MPI_COMM_WORLD, 10, ierr)
    endif

    print *, 'opening ', file_type, 'file ', trim(file)
    ierr=nf90_open(trim(file),nf90_write,f)
    call netcdf_err(ierr, 'opening file: '//trim(file) )
  end subroutine open_command_line_file

  subroutine get_dimensions(f, we_res, sn_res)
    integer, intent(in) :: f
    integer, intent(out) :: we_res, sn_res
    integer :: id_dim

    ierr=nf90_inq_dimid(f, 'west_east', id_dim)
    call netcdf_err(ierr, 'reading west_east' )
    ierr=nf90_inquire_dimension(f,id_dim,len=we_res)
    call netcdf_err(ierr, 'reading west_east' )
    ierr=nf90_inq_dimid(f, 'south_north', id_dim)
    call netcdf_err(ierr, 'reading south_north' )
    ierr=nf90_inquire_dimension(f,id_dim,len=sn_res)
    call netcdf_err(ierr, 'reading south_north' )
  end subroutine get_dimensions


  !--------------------------------------------------------------
  ! if at netcdf call returns an error, print out a message
  ! and stop processing.
  !--------------------------------------------------------------
  subroutine netcdf_err( err, string )
    use mpi
    implicit none

    integer, intent(in) :: err
    character(len=*), intent(in) :: string
    character(len=80) :: errmsg
    integer :: ierr

    if( err == nf90_noerr )return
    errmsg = nf90_strerror(err)
    print*,''
    print*,'fatal error: ', trim(string), ': ', trim(errmsg)
    print*,'stop.'
    call MPI_Abort(MPI_COMM_WORLD, 999, ierr)
  end subroutine netcdf_err


  !--------------------------------------------------------------
  ! Get land sea mask from fv3 restart, and use to create
  ! index for mapping from tiles (FV3 UFS restart) to vector
  !  of land locations (offline Noah-MP restart)
  ! NOTE: slmsk in the restarts counts grid cells as land if
  !       they have a non-zero land fraction. Excludes grid
  !       cells that are surrounded by sea (islands). The slmsk
  !       in the oro_grid files (used by JEDI for screening out
  !       obs is different, and counts grid cells as land if they
  !       are more than 50% land (same exclusion of islands). If
  !       we want to change these definitations, may need to use
  !       land_frac field from the oro_grid files.
  !--------------------------------------------------------------

  ! subroutine get_fv3_mapping(myrank, date_str, hour_str, res, &
  !      len_land_vec, tile2vector)
  !   use mpi
  !   implicit none

  !   integer, intent(in) :: myrank, res
  !   character(len=8), intent(in) :: date_str
  !   character(len=2), intent(in) :: hour_str
  !   integer, allocatable, intent(out) :: tile2vector(:,:)
  !   integer :: len_land_vec

  !   character(len=100) :: restart_file
  !   character(len=1) :: rankch
  !   logical :: file_exists
  !   integer :: ierr, mpierr, ncid
  !   integer :: id_dim, id_var, fres
  !   integer :: slmsk(res,res) ! saved as double in the file, but i think this is OK
  !   integer :: i, j, nn

  !   ! OPEN FILE
  !   write(rankch, '(i1.1)') (myrank+1)
  !   restart_file = date_str//"."//hour_str//"0000.sfc_data.tile"//rankch//".nc"

  !   inquire(file=trim(restart_file), exist=file_exists)

  !   if (.not. file_exists) then
  !      print *, 'restart_file does not exist, ', &
  !           trim(restart_file) , ' exiting'
  !      call MPI_Abort(MPI_COMM_WORLD, 10, mpierr)
  !   endif

  !   write (6, *) 'calculate mapping from land mask in ', trim(restart_file)

  !   ierr=nf90_open(trim(restart_file),nf90_write,ncid)
  !   call netcdf_err(ierr, 'opening file: '//trim(restart_file) )

  !   ! READ MASK and GET MAPPING
  !   ierr=nf90_inq_varid(ncid, "slmsk", id_var)
  !   call netcdf_err(ierr, 'reading slmsk id' )
  !   ierr=nf90_get_var(ncid, id_var, slmsk)
  !   call netcdf_err(ierr, 'reading slmsk' )

  !   ! get number of land points  (note: slmsk is double)
  !   len_land_vec = 0
  !   do i = 1, res
  !      do j = 1, res
  !         if ( slmsk(i,j) == 1)  len_land_vec = len_land_vec+ 1
  !      enddo
  !   enddo

  !   write(6,*) 'Number of land points on rank ', myrank, ' :',  len_land_vec

  !   allocate(tile2vector(len_land_vec,2))

  !   nn=0
  !   do i = 1, res
  !      do j = 1, res
  !         if ( slmsk(i,j) == 1)   then
  !            nn=nn+1
  !            tile2vector(nn,1) = i
  !            tile2vector(nn,2) = j
  !         endif
  !      enddo
  !   enddo

  ! end subroutine get_fv3_mapping


  !--------------------------------------------------------------
  ! open WRF-Hydro restart, and read in required variables
  ! file is opened as read/write and remains open
  !--------------------------------------------------------------
  ! subroutine read_wrf_hydro_restart(myrank, date_str, hour_str, we_res, sn_res, ncid, &
  !      len_land_vec,tile2vector, jedi_state)
  subroutine read_wrf_hydro_restart(f, we_res, sn_res, jedi_state)
    use input_var_names
    use mpi
    implicit none
    integer, intent(in) :: f, we_res, sn_res
    type(jedi_type), intent(inout)  :: jedi_state
    logical :: file_exists
    integer :: ierr, mpierr, id_dim, fwe_res, fsn_res
    integer :: nn

    ! read swe (file name: sheleg, vert dim 1)
    call read_nc_var2D(f, we_res, sn_res, 0, &
         swe_nm, jedi_state%swe)

    ! read snow_depth (file name: snwdph, vert dim 1)
    call read_nc_var2D(f, we_res, sn_res, 0, &
         snow_depth_nm, jedi_state%snow_depth)

    ! ! read active_snow_layers (file name: snowxy, vert dim: 1)
    call read_nc_var2D(f, we_res, sn_res, 0, &
         active_snow_layers_nm, jedi_state%active_snow_layers)
    print *, "WARNING :: check ISNOW equivalent to active_snow_layers"

    ! read swe_previous (file name: sneqvoxy, vert dim: 1)
    call read_nc_var2D(f, we_res, sn_res, 0, &
         swe_previous_nm, jedi_state%swe_previous)

    ! read snow_soil_interface (file name: zsnsoxy, vert dim: 7)
    call read_nc_var3D(f, we_res, sn_res, 7, &
         snow_soil_interface_nm, jedi_state%snow_soil_interface)

    ! read temperature_snow (file name: tsnoxy, vert dim: 3)
    call read_nc_var3D(f, we_res, sn_res, 3, &
         temperature_snow_nm, jedi_state%temperature_snow)

    ! read snow_ice_layer (file name:  snicexy, vert dim: 3)
    call read_nc_var3D(f, we_res, sn_res, 3, &
         snow_ice_layer_nm, jedi_state%snow_ice_layer)

    ! read snow_liq_layer (file name: snliqxy, vert dim: 3)
    call read_nc_var3D(f, we_res, sn_res, 3, &
         snow_liq_layer_nm, jedi_state%snow_liq_layer)

    ! read temperature_soil (file name: stc, use layer 1 only, vert dim: 1)
    call read_nc_var2D(f, we_res, sn_res, 4, &
         temperature_soil_nm, jedi_state%temperature_soil)

  end subroutine read_wrf_hydro_restart

  !--------------------------------------------------------------
  !  read in snow depth increment from jedi increment file
  !  file format is same as restart file
  !--------------------------------------------------------------
  subroutine read_wrf_hydro_increment(f, we_res, sn_res, increment)
    use mpi
    implicit none
    integer, intent(in) :: f, we_res, sn_res
    double precision, intent(out) :: increment(we_res, sn_res)     ! snow depth increment
    integer :: ierr

    ! read snow_depth (file name: snwdph, vert dim 1)
    ! call read_nc_var2D(ncid, len_land_vec, res, tile2vector, 0, &
    !      'snwdph    ', increment)
    ! read snow_depth
    call read_nc_var2D(f, we_res, sn_res, 0, &
         'SNOWH     ', increment)

    ! read snow mass?
    ! call read_nc_var2D(f, we_res, sn_res, 0, &
    !      'SNEQV     ', increment)

    ierr=nf90_close(f)
    call netcdf_err(ierr, 'closing increment file')
  end subroutine  read_wrf_hydro_increment

  !--------------------------------------------------------
  ! Subroutine to read in a 2D variable from netcdf file,
  ! and save to jedi vector
  !--------------------------------------------------------
  ! subroutine read_nc_var2D(ncid, len_land_vec, res, tile2vector, in3D_vdim,  &
  !      var_name, data_vec)
  subroutine read_nc_var2D(ncid, we_res, sn_res, in3D_vdim,  &
       var_name, data)

    integer, intent(in)             :: ncid, we_res, sn_res !, len_land_vec
    character(len=10), intent(in)   :: var_name
    ! integer, intent(in)             :: tile2vector(len_land_vec,2)
    integer, intent(in)             :: in3D_vdim ! 0 - input is 2D,
    ! >0, gives dim of 3rd dimension
    double precision, intent(out)   :: data(we_res,sn_res)

    double precision :: dummy2D(we_res, sn_res)
    double precision, allocatable :: dummy3D(:,:,:)
    integer          :: i, j, ierr, id_var

    ierr=nf90_inq_varid(ncid, trim(var_name), id_var)
    call netcdf_err(ierr, 'reading '//var_name//' id' )

    if (in3D_vdim==0) then
       ierr=nf90_get_var(ncid, id_var, dummy2D)
       call netcdf_err(ierr, 'reading '//var_name//' data' )
    else  ! special case for reading in 3D variable, and retaining only
       ! level 1
       allocate(dummy3D(we_res, in3D_vdim, sn_res))
       ierr=nf90_get_var(ncid, id_var, dummy3D)
       call netcdf_err(ierr, 'reading '//var_name//' data' )
       dummy2D=dummy3D(:,1,:)
    endif

    do j=1,sn_res
       do i=1,we_res
          data(i,j) = dummy2D(i,j)
       enddo
    enddo

  end subroutine read_nc_var2D

  !--------------------------------------------------------
  ! Subroutine to read in a 3D variable from netcdf file,
  ! and save to jedi vector
  !--------------------------------------------------------
  ! subroutine read_nc_var3D(ncid, len_land_vec, res, vdim,  &
  !      tile2vector, var_name, data_vec)
  subroutine read_nc_var3D(ncid, we_res, sn_res, zdim, var_name, data)
    integer, intent(in)             :: ncid, we_res, sn_res, zdim
    character(len=10), intent(in)   :: var_name
    double precision, intent(out)   :: data(we_res, zdim, sn_res)
    ! double precision :: dummy3D(we_res, zdim, sn_res)
    integer          :: ierr, id_var !, nn

    ierr=nf90_inq_varid(ncid, trim(var_name), id_var)
    call netcdf_err(ierr, 'reading '//var_name//' id' )
    ierr=nf90_get_var(ncid, id_var, data) !dummy3D)
    call netcdf_err(ierr, 'reading '//var_name//' data' )

    ! do nn=1,len_land_vec
    !    data_vec(nn,:) = dummy3D(tile2vector(nn,1), tile2vector(nn,2), :)
    ! enddo
  end subroutine read_nc_var3D

  !--------------------------------------------------------------
  ! write updated fields tofv3_restarts  open on ncid
  !--------------------------------------------------------------
  ! subroutine write_fv3_restart(jedi_state, res, ncid, len_land_vec, &
  !      tile2vector)
  subroutine write_wrf_hydro_restart(ncid, we_res, sn_res, jedi_state)
    use input_var_names
    implicit none
    integer, intent(in) :: ncid, we_res, sn_res
    type(jedi_type), intent(in) :: jedi_state

    ! read swe (file name: sheleg, vert dim 1)
    call write_nc_var2D(ncid, we_res, sn_res, 0, &
         swe_nm, jedi_state%swe)

    ! read snow_depth (file name: snwdph, vert dim 1)
    call write_nc_var2D(ncid, we_res, sn_res, 0, &
         snow_depth_nm, jedi_state%snow_depth)

    ! read active_snow_layers (file name: snowxy, vert dim: 1)
    call write_nc_var2D(ncid, we_res, sn_res, 0, &
         active_snow_layers_nm, jedi_state%active_snow_layers)

    ! read swe_previous (file name: sneqvoxy, vert dim: 1)
    call write_nc_var2D(ncid, we_res, sn_res, 0, &
         swe_previous_nm, jedi_state%swe_previous)

    ! read snow_soil_interface (file name: zsnsoxy, vert dim: 7)
    call write_nc_var3D(ncid, we_res, sn_res, 7,  &
         snow_soil_interface_nm, jedi_state%snow_soil_interface)

    ! read temperature_snow (file name: tsnoxy, vert dim: 3)
    call write_nc_var3D(ncid, we_res, sn_res, 3, &
         temperature_snow_nm, jedi_state%temperature_snow)

    ! read snow_ice_layer (file name:  snicexy, vert dim: 3)
    call write_nc_var3D(ncid, we_res, sn_res, 3, &
         snow_ice_layer_nm, jedi_state%snow_ice_layer)

    ! read snow_liq_layer (file name: snliqxy, vert dim: 3)
    call write_nc_var3D(ncid, we_res, sn_res, 3, &
         snow_liq_layer_nm, jedi_state%snow_liq_layer)

    ! read temperature_soil (file name: stc, use layer 1 only, vert dim: 1)
    ! call write_nc_var2D(ncid, we_res, sn_res, 4, &
    !      temperature_soil_nm, jedi_state%temperature_soil)
    print *, "Warning: not writing temperature soil back to restart file"
  end subroutine write_wrf_hydro_restart


  !--------------------------------------------------------
  ! Subroutine to write a 2D variable to the netcdf file
  !--------------------------------------------------------

  subroutine write_nc_var2D(ncid, we_res, sn_res, z_dim, &
       var_name, data)

    integer, intent(in)             :: ncid, we_res, sn_res
    character(len=10), intent(in)   :: var_name
    integer, intent(in)             :: z_dim ! 0 - input is 2D,
    ! >0, gives dim of 3rd dimension
    double precision, intent(in)    :: data(we_res, sn_res)

    ! double precision :: dummy2D(res, res)
    double precision :: dummy3D(we_res, z_dim, sn_res)
    integer          :: nn, ierr, id_var

    ierr=nf90_inq_varid(ncid, trim(var_name), id_var)
    ! call netcdf_err(ierr, 'reading '//trim(var_name)//' id' )
    ! if (z_dim==0) then
    !    ierr=nf90_get_var(ncid, id_var, dummy2D)
    !    call netcdf_err(ierr, 'reading '//trim(var_name)//' data' )
    ! else  ! special case for reading in multi-level variable, and
    !    ! retaining only first level.
    !    ierr=nf90_get_var(ncid, id_var, dummy3D)
    !    call netcdf_err(ierr, 'reading '//trim(var_name)//' data' )
    !    dummy2D = dummy3D(:,:,1)
    ! endif

    ! ! sub in updated locations (retain previous fields for non-land)
    ! do nn=1,len_land_vec
    !    dummy2D(tile2vector(nn,1), tile2vector(nn,2)) = data(nn)
    ! enddo

    ! overwrite
    if (z_dim==0) then
       ierr = nf90_put_var( ncid, id_var, data) !dummy3D)
       call netcdf_err(ierr, 'writing '//trim(var_name) )
    else
       dummy3D(:,1,:) = data
       ierr = nf90_put_var( ncid, id_var, dummy3D)
       call netcdf_err(ierr, 'writing '//trim(var_name) )
    endif
  end subroutine write_nc_var2D

  !--------------------------------------------------------
  ! Subroutine to write a 3D variable to the netcdf file
  !--------------------------------------------------------
  subroutine write_nc_var3D(ncid, we_res, sn_res, zdim, &
       var_name, data)
    integer, intent(in)             :: ncid, we_res, sn_res, zdim
    character(len=10), intent(in)   :: var_name
    double precision, intent(in)    :: data(we_res, zdim, sn_res)
    ! double precision :: dummy3D(we_res, zdim, sn_res)
    integer          :: nn, ierr, id_var

    ierr=nf90_inq_varid(ncid, trim(var_name), id_var)
    ! call netcdf_err(ierr, 'reading '//trim(var_name)//' id' )
    ! ! ierr=nf90_get_var(ncid, id_var, dummy3D)
    ! ierr=nf90_get_var(ncid, id_var, data)
    ! call netcdf_err(ierr, 'reading '//trim(var_name)//' data' )

    ! ! sub in updated locations (retain previous fields for non-land)
    ! do nn=1,len_land_vec
    !    dummy3D(tile2vector(nn,1), tile2vector(nn,2),:) = data(nn,:)
    ! enddo

    ! overwrite
    ierr = nf90_put_var( ncid, id_var, data)
    call netcdf_err(ierr, 'writing '//trim(var_name) )
  end subroutine write_nc_var3D

end program
