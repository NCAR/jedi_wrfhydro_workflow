module input_var_names
  character(len=10), parameter :: swe_nm                 = 'SNEQV'
  character(len=10), parameter :: snow_depth_nm          = 'SNOWH'
  character(len=10), parameter :: active_snow_layers_nm  = 'ISNOW'
  character(len=10), parameter :: swe_previous_nm        = 'SNEQVO'
  character(len=10), parameter :: snow_soil_interface_nm = 'ZSNSO'
  character(len=10), parameter :: temperature_snow_nm    = 'SNOW_T'
  character(len=10), parameter :: snow_ice_layer_nm      = 'SNICE'
  character(len=10), parameter :: snow_liq_layer_nm      = 'SNLIQ'
  character(len=10), parameter :: temperature_soil_nm    = 'SOIL_T'

  ! Old variable names
  ! character(len=10), parameter :: swe_nm                 = 'sheleg'
  ! character(len=10), parameter :: snow_depth_nm          = 'snwdph'
  ! character(len=10), parameter :: active_snow_layers_nm  = 'snowxy'
  ! character(len=10), parameter :: swe_previous_nm        = 'sneqvoxy'
  ! character(len=10), parameter :: snow_soil_interface_nm = 'zsnsoxy'
  ! character(len=10), parameter :: temperature_snow_nm    = 'tsnoxy'
  ! character(len=10), parameter :: snow_ice_layer_nm      = 'snicexy'
  ! character(len=10), parameter :: snow_liq_layer_nm      = 'snliqxy'
  ! character(len=10), parameter :: temperature_soil_nm    = 'stc'
end module input_var_names
