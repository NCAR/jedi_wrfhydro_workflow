module jedi_disag_module
  private
  public jedi_type, updateAllLayers

  type jedi_type
     double precision, allocatable :: swe                (:,:)
     double precision, allocatable :: snow_depth         (:,:)
     double precision, allocatable :: active_snow_layers (:,:)
     double precision, allocatable :: swe_previous       (:,:)
     double precision, allocatable :: snow_soil_interface(:,:,:)
     double precision, allocatable :: temperature_snow   (:,:,:)
     double precision, allocatable :: snow_ice_layer     (:,:,:)
     double precision, allocatable :: snow_liq_layer     (:,:,:)
     double precision, allocatable :: temperature_soil   (:,:)
  end type jedi_type

contains

  subroutine updateAllLayers(we_res, sn_res, increment, jedi)
    integer, intent(in) :: we_res, sn_res
    ! snow depth increment
    double precision, intent(in) :: increment(we_res, sn_res)
    type(jedi_type), intent(inout)   :: jedi

    integer :: i, j, zlayer, zinter, active_layers, vector_loc, pathway
    double precision :: layer_density, swe_increment, liq_ratio
    double precision :: soil_interfaces(7) = (/0.0,0.0,0.0,0.1,0.4,1.0,2.0/)
    double precision :: partition_ratio, layer_depths(3), anal_snow_depth

    associate( &
         swe => jedi%swe                ,&
         snow_depth => jedi%snow_depth         ,&
         active_snow_layers => jedi%active_snow_layers ,&
         swe_previous => jedi%swe_previous       ,&
         snow_soil_interface => jedi%snow_soil_interface,&
         temperature_snow => jedi%temperature_snow   ,&
         snow_ice_layer => jedi%snow_ice_layer     ,&
         snow_liq_layer => jedi%snow_liq_layer     ,&
         temperature_soil => jedi%temperature_soil )

      do j = 1, sn_res
      do i = 1, we_res

         pathway = 0

         anal_snow_depth = snow_depth(i,j) + increment(i,j) ! analysed bulk snow depth

         if(anal_snow_depth <=  0.0001) then ! correct negative snow depth here
            ! also ignore small increments

            swe                (i,j)   = 0.0
            snow_depth         (i,j)   = 0.0
            active_snow_layers (i,j)   = 0.0
            swe_previous       (i,j)   = 0.0
            snow_soil_interface(i,:,j) = (/0.0,0.0,0.0,-0.1,-0.4,-1.0,-2.0/)
            temperature_snow   (i,:,j) = 0.0
            snow_ice_layer     (i,:,j) = 0.0
            snow_liq_layer     (i,:,j) = 0.0

         else

            active_layers = nint(active_snow_layers(i,j))  ! number of active layers (0,-1,-2,-3)

            if(active_layers < 0) then  ! in multi-layer mode

               layer_depths(1) = snow_soil_interface(i,1,j)
               layer_depths(2) = snow_soil_interface(i,2,j) - &
                    snow_soil_interface(i,1,j)
               layer_depths(3) = snow_soil_interface(i,3,j) - &
                    snow_soil_interface(i,2,j)

               if(increment(i,j) > 0.0) then  ! add snow in multi-layer mode

                  pathway = 1

                  vector_loc = 4 + active_layers  ! location in vector of top layer

                  layerloop: do zlayer = vector_loc, 3

                     partition_ratio = -layer_depths(zlayer)/snow_depth(i,j)*1000.d0
                     layer_density = (snow_ice_layer(i,zlayer,j)+snow_liq_layer(i,zlayer,j)) / &
                          (-layer_depths(zlayer))
                     swe_increment = partition_ratio * increment(i,j) * layer_density / 1000.d0
                     liq_ratio = snow_liq_layer(i,zlayer,j) / &
                          ( snow_ice_layer(i,zlayer,j) + snow_liq_layer(i,zlayer,j) )
                     snow_ice_layer(i,zlayer,j) = snow_ice_layer(i,zlayer,j) + &
                          (1.0 - liq_ratio) * swe_increment
                     snow_liq_layer(i,zlayer,j) = snow_liq_layer(i,zlayer,j) + &
                          liq_ratio * swe_increment
                     do zinter = zlayer, 3  ! remove snow from each snow layer
                        snow_soil_interface(i,zinter,j) = snow_soil_interface(i,zinter,j) - &
                             partition_ratio * increment(i,j)/1000.d0
                     end do

                  end do layerloop

               elseif(increment(i,j) < 0.0) then  ! remove snow in multi-layer mode

                  pathway = 2

                  vector_loc = 4 + active_layers  ! location in vector of top layer

                  do zlayer = vector_loc, 3

                     partition_ratio = -layer_depths(zlayer)/snow_depth(i,j)*1000.d0
                     layer_density = (snow_ice_layer(i,zlayer,j)+snow_liq_layer(i,zlayer,j)) / &
                          (-layer_depths(zlayer))
                     swe_increment = partition_ratio * increment(i,j) * layer_density / 1000.d0
                     liq_ratio = snow_liq_layer(i,zlayer,j) / &
                          ( snow_ice_layer(i,zlayer,j) + snow_liq_layer(i,zlayer,j) )
                     snow_ice_layer(i,zlayer,j) = snow_ice_layer(i,zlayer,j) + &
                          (1.0 - liq_ratio) * swe_increment
                     snow_liq_layer(i,zlayer,j) = snow_liq_layer(i,zlayer,j) + &
                          liq_ratio * swe_increment
                     do zinter = zlayer, 3  ! remove snow from each snow layer
                        snow_soil_interface(i,zinter,j) = snow_soil_interface(i,zinter,j) - &
                             partition_ratio * increment(i,j)/1000.d0
                     end do

                  end do ! layerloop

               end if  ! increment

               ! For multi-layer mode, recalculate interfaces and sum depth/swe

               do zlayer = 4, 7
                  snow_soil_interface(i,zlayer,j) = snow_soil_interface(i,3,j) - soil_interfaces(zlayer)
               end do

               snow_depth(i,j) = -snow_soil_interface(i,3,j) * 1000.d0

               swe(i,j) = 0.0

               do zlayer = 1, 3
                  swe(i,j) = swe(i,j) + snow_ice_layer(i,zlayer,j) + snow_liq_layer(i,zlayer,j)
               end do

               swe_previous(i,j) = swe(i,j)

               if(snow_depth(i,j) < 25.d0) then  ! go out of multi-layer mode
                  active_snow_layers (i,j) = 0.d0
                  snow_soil_interface(i,:,j) = (/0.0,0.0,0.0,-0.1,-0.4,-1.0,-2.0/)
                  temperature_snow   (i,:,j) = 0.0
                  snow_ice_layer     (i,:,j) = 0.0
                  snow_liq_layer     (i,:,j) = 0.0
               end if

            elseif(active_layers == 0) then  ! snow starts in zero-layer mode

               if(increment(i,j) > 0.0) then  ! add snow in zero-layer mode

                  if(snow_depth(i,j) == 0) then   ! no snow present, so assume density based on soil temperature
                     pathway = 3
                     layer_density = max(80.0,min(120.,67.92+51.25*exp((temperature_soil(i,j)-273.15)/2.59)))
                  else   ! use existing density
                     pathway = 4
                     layer_density = swe(i,j) / snow_depth(i,j) * 1000.d0
                  end if
                  snow_depth(i,j) = snow_depth(i,j) + increment(i,j)
                  swe(i,j) = swe(i,j) + increment(i,j) * layer_density / 1000.d0
                  swe_previous(i,j) = swe(i,j)

                  active_snow_layers(i,j)      = 0.0
                  snow_ice_layer(i,:,j)        = 0.0
                  snow_liq_layer(i,:,j)        = 0.0
                  temperature_snow(i,:,j)      = 0.0
                  snow_soil_interface(i,1:3,j) = 0.0

                  if(snow_depth(i,j) > 25.0) then  ! snow depth is > 25mm so put in a layer
                     pathway = 5
                     active_snow_layers(i,j) = -1.0
                     snow_ice_layer(i,3,j)   = swe(i,j)
                     temperature_snow(i,3,j) = temperature_soil(i,j)
                     do zlayer = 3, 7
                        snow_soil_interface(i,zlayer,j) = snow_soil_interface(i,zlayer,j) - snow_depth(i,j)/1000.d0
                     end do
                  end if

               elseif(increment(i,j) < 0.0) then  ! remove snow in zero-layer mode

                  pathway = 6

                  layer_density = swe(i,j) / snow_depth(i,j) * 1000.d0
                  snow_depth(i,j) = snow_depth(i,j) + increment(i,j)
                  swe(i,j) = swe(i,j) + increment(i,j) * layer_density / 1000.d0
                  swe_previous(i,j) = swe(i,j)

                  active_snow_layers(i,j)      = 0.0
                  snow_ice_layer(i,:,j)        = 0.0
                  snow_liq_layer(i,:,j)        = 0.0
                  temperature_snow(i,:,j)      = 0.0
                  snow_soil_interface(i,1:3,j) = 0.0

               end if  ! increment

            end if  ! active_layers

         end if  ! anal_snow_depth <= 0.

         ! do some gross checks

         if(abs(snow_soil_interface(i,7,j) - snow_soil_interface(i,3,j) + 2.d0) > 0.0000001) then
            print*, "Depth of soil not 2m"
            print*, pathway
            print*, snow_soil_interface(i,7,j), snow_soil_interface(i,3,j)
            !      stop
         end if

         if(active_snow_layers(i,j) < 0.0 .and. abs(snow_depth(i,j) + 1000.d0*snow_soil_interface(i,3,j)) > 0.0000001) then
            print*, "snow_depth and snow_soil_interface inconsistent"
            print*, pathway
            print*, active_snow_layers(i,j), snow_depth(i,j), snow_soil_interface(i,3,j)
            !      stop
         end if

         if( (abs(anal_snow_depth - snow_depth(i,j))   > 0.0000001) .and. (anal_snow_depth > 0.0001) ) then
            print*, "snow increment and updated model snow inconsistent"
            print*, pathway
            print*, anal_snow_depth, snow_depth(i,j)
            !      stop
         end if

         if(snow_depth(i,j) < 0.0 .or. snow_soil_interface(i,3,j) > 0.0 ) then
            print*, "snow increment and updated model snow inconsistent"
            print*, pathway
            print*, snow_depth(i,j), snow_soil_interface(i,3,j)
            !      stop
         end if
      end do
      end do

    end associate

  end subroutine updateAllLayers

end module jedi_disag_module
