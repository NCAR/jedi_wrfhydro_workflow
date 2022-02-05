program jedi_snow_incr
  use netcdf
  use mpi
  use jedi_disag_module, only : jedi_type, updateAllLayers
  implicit none

  type(jedi_type) :: jedi_state
  integer :: we_res, sn_res, len_land_vec
  character(len=8) :: date_str
  character(len=2) :: hour_str
  ! index to map between tile and vector space
  integer, allocatable :: tile2vector(:,:)
  double precision, allocatable :: increment(:,:)
  integer :: ierr, nprocs, myrank, lunit, ncid
  logical :: file_exists

  namelist /jedi_snow/ date_str, hour_str, we_res ,sn_res

  call MPI_Init(ierr)
  call MPI_Comm_size(MPI_COMM_WORLD, nprocs, ierr)
  call MPI_Comm_rank(MPI_COMM_WORLD, myrank, ierr)

  print*
  print*,"starting apply_incr_jedi_snow program on rank ", myrank

  ! READ NAMELIST
  inquire (file='apply_incr_nml', exist=file_exists)
  if (.not. file_exists) then
     write (6, *) 'ERROR: apply_incr_nml does not exist'
     call MPI_Abort(MPI_COMM_WORLD, 10, ierr)
  end if

  open (action='read', file='apply_incr_nml', iostat=ierr, newunit=lunit)
  read (nml=jedi_snow, iostat=ierr, unit=lunit)


  ! GET MAPPING INDEX (see subroutine comments re: source of land/sea mask)
  ! call get_fv3_mapping(myrank, date_str, hour_str, res, len_land_vec, tile2vector)

  ! SET-UP THE JEDI STATE AND INCREMENT
  allocate(jedi_state%swe(we_res, sn_res))
  allocate(increment(we_res, sn_res))
  ! allocate(jedi_state%snow_depth         (len_land_vec))
  ! allocate(jedi_state%active_snow_layers (len_land_vec))
  ! allocate(jedi_state%swe_previous       (len_land_vec))
  ! allocate(jedi_state%snow_soil_interface(len_land_vec,7))
  ! allocate(jedi_state%temperature_snow   (len_land_vec,3))
  ! allocate(jedi_state%snow_ice_layer     (len_land_vec,3))
  ! allocate(jedi_state%snow_liq_layer     (len_land_vec,3))
  ! allocate(jedi_state%temperature_soil   (len_land_vec))
  ! allocate(increment   (len_land_vec))

  ! READ RESTART FILE
  call read_wrf_hydro_restart(myrank, date_str, hour_str, we_res, &
       sn_res, ncid, jedi_state )

  ! READ SNOW DEPTH INCREMENT
  call read_wrf_hydro_increment(myrank, date_str, hour_str, we_res, &
       sn_res, increment)

  ! ADJUST THE RESTART
  print *, "WARNING :: ADD UPDATEALLLAYERS BACK IN!!"
  ! call updateAllLayers(len_land_vec, increment, jedi_state)

  ! WRITE OUT ADJUSTED RESTART
  print *, "WARNING :: ADD AND FIND WRITE_WRF_HYDRO_RESTART BACK IN!!"
  ! call write_wrf_hydro_restart(jedi_state, we_res, sn_res, ncid)!, len_land_vec, &
       ! tile2vector)


  ! CLOSE RESTART FILE
  print*
  print*,"closing restart, apply_incr_jedi_snow program on rank ", myrank
  ierr = nf90_close(ncid)

  call MPI_Finalize(ierr)

contains

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
  ! open fv3 restart, and read in required variables
  ! file is opened as read/write and remains open
  !--------------------------------------------------------------
  ! subroutine read_wrf_hydro_restart(myrank, date_str, hour_str, we_res, sn_res, ncid, &
  !      len_land_vec,tile2vector, jedi_state)
  subroutine read_wrf_hydro_restart(myrank, date_str, hour_str, we_res, &
       sn_res, ncid, jedi_state)
    use mpi
    implicit none

    integer, intent(in) :: myrank, we_res, sn_res !, len_land_vec
    character(len=8), intent(in) :: date_str
    character(len=2), intent(in) :: hour_str
    ! integer, intent(in) :: tile2vector(len_land_vec,2)

    integer, intent(out) :: ncid
    type(jedi_type), intent(inout)  :: jedi_state

    character(len=100) :: restart_file
    character(len=1) :: rankch
    logical :: file_exists
    integer :: ierr, mpierr, id_dim, fwe_res, fsn_res
    integer :: nn

    ! OPEN FILE
    write(rankch, '(i1.1)') (myrank+1)
    ! restart_file = &
    ! date_str//"."//hour_str//"0000.sfc_data.tile"//rankch//".nc"
    restart_file = "RESTART."//date_str//hour_str//"_DOMAIN1"
    ! print *, "RESTART_FILE=", RESTART_FILE

    inquire(file=trim(restart_file), exist=file_exists)

    if (.not. file_exists) then
       print *, 'restart_file does not exist, ', &
            trim(restart_file) , ' exiting'
       call MPI_Abort(MPI_COMM_WORLD, 10, mpierr)
    endif

    write (6, *) 'opening ', trim(restart_file)

    ierr=nf90_open(trim(restart_file),nf90_write,ncid)
    call netcdf_err(ierr, 'opening file: '//trim(restart_file) )

    ! CHECK DIMENSIONS
    ! ierr=nf90_inq_dimid(ncid, 'xaxis_1', id_dim)
    ! call netcdf_err(ierr, 'reading xaxis_1' )
    ! ierr=nf90_inquire_dimension(ncid,id_dim,len=fres)
    ! call netcdf_err(ierr, 'reading xaxis_1' )
    ierr=nf90_inq_dimid(ncid, 'west_east', id_dim)
    call netcdf_err(ierr, 'reading west_east' )
    ierr=nf90_inquire_dimension(ncid,id_dim,len=fwe_res)
    call netcdf_err(ierr, 'reading west_east' )

    ierr=nf90_inq_dimid(ncid, 'south_north', id_dim)
    call netcdf_err(ierr, 'reading south_north' )
    ierr=nf90_inquire_dimension(ncid,id_dim,len=fsn_res)
    call netcdf_err(ierr, 'reading south_north' )

    if ( fwe_res /= we_res .or. fsn_res /= sn_res) then
       print*,'fatal error: dimensions wrong.'
       call MPI_Abort(MPI_COMM_WORLD, ierr, mpierr)
    endif


    ! read swe (file name: sheleg, vert dim 1)
    call read_nc_var2D(ncid, we_res, sn_res, 0, &
         'SNEQV     ', jedi_state%swe)

    ! ! read swe (file name: sheleg, vert dim 1)
    ! call read_nc_var2D(ncid, len_land_vec, res, tile2vector, 0, &
    !      'sheleg    ', jedi_state%swe)

    ! ! read snow_depth (file name: snwdph, vert dim 1)
    ! call read_nc_var2D(ncid, len_land_vec, res, tile2vector, 0, &
    !      'snwdph    ', jedi_state%snow_depth)

    ! ! read active_snow_layers (file name: snowxy, vert dim: 1)
    ! call read_nc_var2D(ncid, len_land_vec, res, tile2vector, 0, &
    !      'snowxy    ', jedi_state%active_snow_layers)

    ! ! read swe_previous (file name: sneqvoxy, vert dim: 1)
    ! call read_nc_var2D(ncid, len_land_vec, res, tile2vector, 0, &
    !      'sneqvoxy  ', jedi_state%swe_previous)

    ! ! read snow_soil_interface (file name: zsnsoxy, vert dim: 7)
    ! call read_nc_var3D(ncid, len_land_vec, res, 7,  tile2vector, &
    !      'zsnsoxy   ', jedi_state%snow_soil_interface)

    ! ! read temperature_snow (file name: tsnoxy, vert dim: 3)
    ! call read_nc_var3D(ncid, len_land_vec, res, 3, tile2vector, &
    !      'tsnoxy    ', jedi_state%temperature_snow)

    ! ! read snow_ice_layer (file name:  snicexy, vert dim: 3)
    ! call read_nc_var3D(ncid, len_land_vec, res, 3, tile2vector, &
    !      'snicexy    ', jedi_state%snow_ice_layer)

    ! ! read snow_liq_layer (file name: snliqxy, vert dim: 3)
    ! call read_nc_var3D(ncid, len_land_vec, res, 3, tile2vector, &
    !      'snliqxy   ', jedi_state%snow_liq_layer)

    ! ! read temperature_soil (file name: stc, use layer 1 only, vert dim: 1)
    ! call read_nc_var2D(ncid, len_land_vec, res, tile2vector, 4, &
    !      'stc       ', jedi_state%temperature_soil)

  end subroutine read_wrf_hydro_restart

  !--------------------------------------------------------------
  !  read in snow depth increment from jedi increment file
  !  file format is same as restart file
  !--------------------------------------------------------------
  subroutine read_wrf_hydro_increment(myrank, date_str, hour_str, we_res, &
       sn_res, increment)
    use mpi
    implicit none

    integer, intent(in) :: myrank, we_res, sn_res
    character(len=8), intent(in) :: date_str
    character(len=2), intent(in) :: hour_str
    ! integer, intent(in) :: tile2vector(len_land_vec,2)
    double precision, intent(out) :: increment(we_res, sn_res)     ! snow depth increment

    character(len=100) :: incr_file
    character(len=1) :: rankch
    logical :: file_exists
    integer :: ierr, mpierr
    integer :: id_dim, id_var, fwe_res, fsn_res, ncid
    integer :: nn

    ! OPEN FILE
    write(rankch, '(i1.1)') (myrank+1)
    ! incr_file = date_str//"."//hour_str//"0000.xainc.sfc_data.tile"//rankch//".nc"
    incr_file = "INCREMENT."//date_str//hour_str//"_DOMAIN1"
    print *, "WARNING :: FOR TESTING INCREMENT FILE IS ", incr_file

    inquire(file=trim(incr_file), exist=file_exists)

    if (.not. file_exists) then
       print *, 'incr_file does not exist, ', &
            trim(incr_file) , ' exiting'
       call MPI_Abort(MPI_COMM_WORLD, 10, mpierr)
    endif

    write (6, *) 'opening ', trim(incr_file)

    ierr=nf90_open(trim(incr_file),nf90_write,ncid)
    call netcdf_err(ierr, 'opening file: '//trim(incr_file) )

    ! CHECK DIMENSIONS
    ! ierr=nf90_inq_dimid(ncid, 'xaxis_1', id_dim)
    ! call netcdf_err(ierr, 'reading xaxis_1' )
    ! ierr=nf90_inquire_dimension(ncid,id_dim,len=fres)
    ! call netcdf_err(ierr, 'reading xaxis_1' )
    ierr=nf90_inq_dimid(ncid, 'west_east', id_dim)
    call netcdf_err(ierr, 'reading west_east' )
    ierr=nf90_inquire_dimension(ncid,id_dim,len=fwe_res)
    call netcdf_err(ierr, 'reading west_east' )

    ierr=nf90_inq_dimid(ncid, 'south_north', id_dim)
    call netcdf_err(ierr, 'reading south_north' )
    ierr=nf90_inquire_dimension(ncid,id_dim,len=fsn_res)
    call netcdf_err(ierr, 'reading south_north' )

    if ( fwe_res /= we_res .or. fsn_res /= sn_res) then
       print*,'fatal error: dimensions wrong.'
       call MPI_Abort(MPI_COMM_WORLD, ierr, mpierr)
    endif

    ! read snow_depth (file name: snwdph, vert dim 1)
    ! call read_nc_var2D(ncid, len_land_vec, res, tile2vector, 0, &
    !      'snwdph    ', increment)
    call read_nc_var2D(ncid, we_res, sn_res, 0, &
         'SNEQV     ', jedi_state%swe)

    ! close file
    write (6, *) 'closing ', trim(incr_file)

    ierr=nf90_close(ncid)
    call netcdf_err(ierr, 'closing file: '//trim(incr_file) )

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
    double precision :: dummy3D(we_res, sn_res, in3D_vdim)
    integer          :: i, j, ierr, id_var

    ierr=nf90_inq_varid(ncid, trim(var_name), id_var)
    call netcdf_err(ierr, 'reading '//var_name//' id' )

    if (in3D_vdim==0) then
       ierr=nf90_get_var(ncid, id_var, dummy2D)
       call netcdf_err(ierr, 'reading '//var_name//' data' )
    else  ! special case for reading in 3D variable, and retaining only
       ! level 1
       ierr=nf90_get_var(ncid, id_var, dummy3D)
       call netcdf_err(ierr, 'reading '//var_name//' data' )
       dummy2D=dummy3D(:,:,1)
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

  subroutine read_nc_var3D(ncid, len_land_vec, res, vdim,  &
       tile2vector, var_name, data_vec)

    integer, intent(in)             :: ncid, len_land_vec, res, vdim
    character(len=10), intent(in)   :: var_name
    integer, intent(in)             :: tile2vector(len_land_vec,2)
    double precision, intent(out)   :: data_vec(len_land_vec, vdim)

    double precision :: dummy3D(res, res, vdim)
    integer          :: nn, ierr, id_var

    ierr=nf90_inq_varid(ncid, trim(var_name), id_var)
    call netcdf_err(ierr, 'reading '//var_name//' id' )
    ierr=nf90_get_var(ncid, id_var, dummy3D)
    call netcdf_err(ierr, 'reading '//var_name//' data' )

    do nn=1,len_land_vec
       data_vec(nn,:) = dummy3D(tile2vector(nn,1), tile2vector(nn,2), :)
    enddo

  end subroutine read_nc_var3D

  !--------------------------------------------------------------
  ! write updated fields tofv3_restarts  open on ncid
  !--------------------------------------------------------------
  subroutine write_fv3_restart(jedi_state, res, ncid, len_land_vec, &
       tile2vector)

    implicit none

    integer, intent(in) :: ncid, res, len_land_vec
    type(jedi_type), intent(in) :: jedi_state
    integer, intent(in) :: tile2vector(len_land_vec,2)


    ! read swe (file name: sheleg, vert dim 1)
    call write_nc_var2D(ncid, len_land_vec, res, tile2vector, 0, &
         'sheleg    ', jedi_state%swe)

    ! read snow_depth (file name: snwdph, vert dim 1)
    call write_nc_var2D(ncid, len_land_vec, res, tile2vector, 0, &
         'snwdph    ', jedi_state%snow_depth)

    ! read active_snow_layers (file name: snowxy, vert dim: 1)
    call write_nc_var2D(ncid, len_land_vec, res, tile2vector, 0, &
         'snowxy    ', jedi_state%active_snow_layers)

    ! read swe_previous (file name: sneqvoxy, vert dim: 1)
    call write_nc_var2D(ncid, len_land_vec, res, tile2vector, 0, &
         'sneqvoxy  ', jedi_state%swe_previous)

    ! read snow_soil_interface (file name: zsnsoxy, vert dim: 7)
    call write_nc_var3D(ncid, len_land_vec, res, 7,  tile2vector, &
         'zsnsoxy   ', jedi_state%snow_soil_interface)

    ! read temperature_snow (file name: tsnoxy, vert dim: 3)
    call write_nc_var3D(ncid, len_land_vec, res, 3, tile2vector, &
         'tsnoxy    ', jedi_state%temperature_snow)

    ! read snow_ice_layer (file name:  snicexy, vert dim: 3)
    call write_nc_var3D(ncid, len_land_vec, res, 3, tile2vector, &
         'snicexy    ', jedi_state%snow_ice_layer)

    ! read snow_liq_layer (file name: snliqxy, vert dim: 3)
    call write_nc_var3D(ncid, len_land_vec, res, 3, tile2vector, &
         'snliqxy   ', jedi_state%snow_liq_layer)

    ! read temperature_soil (file name: stc, use layer 1 only, vert dim: 1)
    call write_nc_var2D(ncid, len_land_vec, res, tile2vector, 4, &
         'stc       ', jedi_state%temperature_soil)


  end subroutine write_fv3_restart


  !--------------------------------------------------------
  ! Subroutine to write a 2D variable to the netcdf file
  !--------------------------------------------------------

  subroutine write_nc_var2D(ncid, len_land_vec, res, tile2vector,   &
       in3D_vdim, var_name, data_vec)

    integer, intent(in)             :: ncid, len_land_vec, res
    character(len=10), intent(in)   :: var_name
    integer, intent(in)             :: tile2vector(len_land_vec,2)
    integer, intent(in)             :: in3D_vdim ! 0 - input is 2D,
    ! >0, gives dim of 3rd dimension
    double precision, intent(in)    :: data_vec(len_land_vec)

    double precision :: dummy2D(res, res)
    double precision :: dummy3D(res, res, in3D_vdim)
    integer          :: nn, ierr, id_var

    ierr=nf90_inq_varid(ncid, trim(var_name), id_var)
    call netcdf_err(ierr, 'reading '//trim(var_name)//' id' )
    if (in3D_vdim==0) then
       ierr=nf90_get_var(ncid, id_var, dummy2D)
       call netcdf_err(ierr, 'reading '//trim(var_name)//' data' )
    else  ! special case for reading in multi-level variable, and
       ! retaining only first level.
       ierr=nf90_get_var(ncid, id_var, dummy3D)
       call netcdf_err(ierr, 'reading '//trim(var_name)//' data' )
       dummy2D = dummy3D(:,:,1)
    endif

    ! sub in updated locations (retain previous fields for non-land)
    do nn=1,len_land_vec
       dummy2D(tile2vector(nn,1), tile2vector(nn,2)) = data_vec(nn)
    enddo

    ! overwrite
    if (in3D_vdim==0) then
       ierr = nf90_put_var( ncid, id_var, dummy2D)
       call netcdf_err(ierr, 'writing '//trim(var_name) )
    else
       dummy3D(:,:,1) = dummy2D
       ierr = nf90_put_var( ncid, id_var, dummy3D)
       call netcdf_err(ierr, 'writing '//trim(var_name) )
    endif

  end subroutine write_nc_var2D

  !--------------------------------------------------------
  ! Subroutine to write a 3D variable to the netcdf file
  !--------------------------------------------------------

  subroutine write_nc_var3D(ncid, len_land_vec, res, vdim, &
       tile2vector, var_name, data_vec)

    integer, intent(in)             :: ncid, len_land_vec, res, vdim
    character(len=10), intent(in)   :: var_name
    integer, intent(in)             :: tile2vector(len_land_vec,2)
    double precision, intent(in)    :: data_vec(len_land_vec, vdim)

    double precision :: dummy3D(res, res, vdim)
    integer          :: nn, ierr, id_var

    ierr=nf90_inq_varid(ncid, trim(var_name), id_var)
    call netcdf_err(ierr, 'reading '//trim(var_name)//' id' )
    ierr=nf90_get_var(ncid, id_var, dummy3D)
    call netcdf_err(ierr, 'reading '//trim(var_name)//' data' )

    ! sub in updated locations (retain previous fields for non-land)
    do nn=1,len_land_vec
       dummy3D(tile2vector(nn,1), tile2vector(nn,2),:) = data_vec(nn,:)
    enddo

    ! overwrite
    ierr = nf90_put_var( ncid, id_var, dummy3D)
    call netcdf_err(ierr, 'writing '//trim(var_name) )

  end subroutine write_nc_var3D

end program
