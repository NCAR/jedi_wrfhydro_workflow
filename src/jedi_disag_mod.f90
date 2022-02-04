module jedi_disag_module
  private
  public jedi_type, UpdateAllLayers

  type jedi_type
     double precision, allocatable :: swe                (:)
     double precision, allocatable :: snow_depth         (:)
     double precision, allocatable :: active_snow_layers (:)
     double precision, allocatable :: swe_previous       (:)
     double precision, allocatable :: snow_soil_interface(:,:)
     double precision, allocatable :: temperature_snow   (:,:)
     double precision, allocatable :: snow_ice_layer     (:,:)
     double precision, allocatable :: snow_liq_layer     (:,:)
     double precision, allocatable :: temperature_soil   (:)
  end type jedi_type

contains

  subroutine updateAllLayers(vector_length, increment, jedi)
    integer, intent(in) :: vector_length
    double precision, intent(in) :: increment(vector_length) ! snow depth increment
    type(jedi_type), intent(inout)   :: jedi

    integer :: iloc, ilayer, iinter, active_layers, vector_loc, pathway
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

      do iloc = 1, vector_length

         pathway = 0

         anal_snow_depth = snow_depth(iloc) + increment(iloc) ! analysed bulk snow depth

         if(anal_snow_depth <=  0.0001) then ! correct negative snow depth here
            ! also ignore small increments

            swe                (iloc)   = 0.0
            snow_depth         (iloc)   = 0.0
            active_snow_layers (iloc)   = 0.0
            swe_previous       (iloc)   = 0.0
            snow_soil_interface(iloc,:) = (/0.0,0.0,0.0,-0.1,-0.4,-1.0,-2.0/)
            temperature_snow   (iloc,:) = 0.0
            snow_ice_layer     (iloc,:) = 0.0
            snow_liq_layer     (iloc,:) = 0.0

         else

            active_layers = nint(active_snow_layers(iloc))  ! number of active layers (0,-1,-2,-3)

            if(active_layers < 0) then  ! in multi-layer mode

               layer_depths(1) = snow_soil_interface(iloc,1)
               layer_depths(2) = snow_soil_interface(iloc,2)-snow_soil_interface(iloc,1)
               layer_depths(3) = snow_soil_interface(iloc,3)-snow_soil_interface(iloc,2)

               if(increment(iloc) > 0.0) then  ! add snow in multi-layer mode

                  pathway = 1

                  vector_loc = 4 + active_layers  ! location in vector of top layer

                  layerloop: do ilayer = vector_loc, 3

                     partition_ratio = -layer_depths(ilayer)/snow_depth(iloc)*1000.d0
                     layer_density = (snow_ice_layer(iloc,ilayer)+snow_liq_layer(iloc,ilayer)) / &
                          (-layer_depths(ilayer))
                     swe_increment = partition_ratio * increment(iloc) * layer_density / 1000.d0
                     liq_ratio = snow_liq_layer(iloc,ilayer) / &
                          ( snow_ice_layer(iloc,ilayer) + snow_liq_layer(iloc,ilayer) )
                     snow_ice_layer(iloc,ilayer) = snow_ice_layer(iloc,ilayer) + &
                          (1.0 - liq_ratio) * swe_increment
                     snow_liq_layer(iloc,ilayer) = snow_liq_layer(iloc,ilayer) + &
                          liq_ratio * swe_increment
                     do iinter = ilayer, 3  ! remove snow from each snow layer
                        snow_soil_interface(iloc,iinter) = snow_soil_interface(iloc,iinter) - &
                             partition_ratio * increment(iloc)/1000.d0
                     end do

                  end do layerloop

               elseif(increment(iloc) < 0.0) then  ! remove snow in multi-layer mode

                  pathway = 2

                  vector_loc = 4 + active_layers  ! location in vector of top layer

                  do ilayer = vector_loc, 3

                     partition_ratio = -layer_depths(ilayer)/snow_depth(iloc)*1000.d0
                     layer_density = (snow_ice_layer(iloc,ilayer)+snow_liq_layer(iloc,ilayer)) / &
                          (-layer_depths(ilayer))
                     swe_increment = partition_ratio * increment(iloc) * layer_density / 1000.d0
                     liq_ratio = snow_liq_layer(iloc,ilayer) / &
                          ( snow_ice_layer(iloc,ilayer) + snow_liq_layer(iloc,ilayer) )
                     snow_ice_layer(iloc,ilayer) = snow_ice_layer(iloc,ilayer) + &
                          (1.0 - liq_ratio) * swe_increment
                     snow_liq_layer(iloc,ilayer) = snow_liq_layer(iloc,ilayer) + &
                          liq_ratio * swe_increment
                     do iinter = ilayer, 3  ! remove snow from each snow layer
                        snow_soil_interface(iloc,iinter) = snow_soil_interface(iloc,iinter) - &
                             partition_ratio * increment(iloc)/1000.d0
                     end do

                  end do ! layerloop

               end if  ! increment

               ! For multi-layer mode, recalculate interfaces and sum depth/swe

               do ilayer = 4, 7
                  snow_soil_interface(iloc,ilayer) = snow_soil_interface(iloc,3) - soil_interfaces(ilayer)
               end do

               snow_depth(iloc) = -snow_soil_interface(iloc,3) * 1000.d0

               swe(iloc) = 0.0

               do ilayer = 1, 3
                  swe(iloc) = swe(iloc) + snow_ice_layer(iloc,ilayer) + snow_liq_layer(iloc,ilayer)
               end do

               swe_previous(iloc) = swe(iloc)

               if(snow_depth(iloc) < 25.d0) then  ! go out of multi-layer mode
                  active_snow_layers (iloc) = 0.d0
                  snow_soil_interface(iloc,:) = (/0.0,0.0,0.0,-0.1,-0.4,-1.0,-2.0/)
                  temperature_snow   (iloc,:) = 0.0
                  snow_ice_layer     (iloc,:) = 0.0
                  snow_liq_layer     (iloc,:) = 0.0
               end if

            elseif(active_layers == 0) then  ! snow starts in zero-layer mode

               if(increment(iloc) > 0.0) then  ! add snow in zero-layer mode

                  if(snow_depth(iloc) == 0) then   ! no snow present, so assume density based on soil temperature
                     pathway = 3
                     layer_density = max(80.0,min(120.,67.92+51.25*exp((temperature_soil(iloc)-273.15)/2.59)))
                  else   ! use existing density
                     pathway = 4
                     layer_density = swe(iloc) / snow_depth(iloc) * 1000.d0
                  end if
                  snow_depth(iloc) = snow_depth(iloc) + increment(iloc)
                  swe(iloc) = swe(iloc) + increment(iloc) * layer_density / 1000.d0
                  swe_previous(iloc) = swe(iloc)

                  active_snow_layers(iloc)      = 0.0
                  snow_ice_layer(iloc,:)        = 0.0
                  snow_liq_layer(iloc,:)        = 0.0
                  temperature_snow(iloc,:)      = 0.0
                  snow_soil_interface(iloc,1:3) = 0.0

                  if(snow_depth(iloc) > 25.0) then  ! snow depth is > 25mm so put in a layer
                     pathway = 5
                     active_snow_layers(iloc) = -1.0
                     snow_ice_layer(iloc,3)   = swe(iloc)
                     temperature_snow(iloc,3) = temperature_soil(iloc)
                     do ilayer = 3, 7
                        snow_soil_interface(iloc,ilayer) = snow_soil_interface(iloc,ilayer) - snow_depth(iloc)/1000.d0
                     end do
                  end if

               elseif(increment(iloc) < 0.0) then  ! remove snow in zero-layer mode

                  pathway = 6

                  layer_density = swe(iloc) / snow_depth(iloc) * 1000.d0
                  snow_depth(iloc) = snow_depth(iloc) + increment(iloc)
                  swe(iloc) = swe(iloc) + increment(iloc) * layer_density / 1000.d0
                  swe_previous(iloc) = swe(iloc)

                  active_snow_layers(iloc)      = 0.0
                  snow_ice_layer(iloc,:)        = 0.0
                  snow_liq_layer(iloc,:)        = 0.0
                  temperature_snow(iloc,:)      = 0.0
                  snow_soil_interface(iloc,1:3) = 0.0

               end if  ! increment

            end if  ! active_layers

         end if  ! anal_snow_depth <= 0.

         ! do some gross checks

         if(abs(snow_soil_interface(iloc,7) - snow_soil_interface(iloc,3) + 2.d0) > 0.0000001) then
            print*, "Depth of soil not 2m"
            print*, pathway
            print*, snow_soil_interface(iloc,7), snow_soil_interface(iloc,3)
            !      stop
         end if

         if(active_snow_layers(iloc) < 0.0 .and. abs(snow_depth(iloc) + 1000.d0*snow_soil_interface(iloc,3)) > 0.0000001) then
            print*, "snow_depth and snow_soil_interface inconsistent"
            print*, pathway
            print*, active_snow_layers(iloc), snow_depth(iloc), snow_soil_interface(iloc,3)
            !      stop
         end if

         if( (abs(anal_snow_depth - snow_depth(iloc))   > 0.0000001) .and. (anal_snow_depth > 0.0001) ) then
            print*, "snow increment and updated model snow inconsistent"
            print*, pathway
            print*, anal_snow_depth, snow_depth(iloc)
            !      stop
         end if

         if(snow_depth(iloc) < 0.0 .or. snow_soil_interface(iloc,3) > 0.0 ) then
            print*, "snow increment and updated model snow inconsistent"
            print*, pathway
            print*, snow_depth(iloc), snow_soil_interface(iloc,3)
            !      stop
         end if

      end do

    end associate

  end subroutine updateAllLayers

end module jedi_disag_module
