#*******************************************************************************
#  This is to cut out the RESTART files for a cut out domain from NWM domain
#*******************************************************************************

# Provide the Path to necessary  files
library(rwrfhydro)
library(ncdf4)

# Coordinate parameter text file
subCoordParamFile <- "/glade/work/mazrooei/jedi/ctest_jedi_workflow/site_09253000/params.txt"

# Route link file
fullRtlinkFile <- "/glade/p/cisl/nwc/nwmv21_finals/CONUS/DOMAIN_FinalParams/RouteLink_NWMv2.1.nc"
# Route link file
subRtlinkFile <- "/glade/work/mazrooei/jedi/ctest_jedi_workflow/site_09253000/Domain/Route_Link.nc"

# LSM RESTART file
lsmRestartFile <- "/glade/scratch/mazrooei/DATA/RESTARTs_NWM_MR_2021/202103/nwm.rst.00.2021030100/RESTART.2021030100_DOMAIN1"
# LSM RESESTART subset file
subLsmRestartFile <- "/glade/work/mazrooei/jedi/ctest_jedi_workflow/site_09253000/Restart/RESTART.2021030100.nc"

# HYDRO RESTART file
hydroReasratFile <- "/glade/scratch/mazrooei/DATA/RESTARTs_NWM_MR_2021/202103/nwm.rst.00.2021030100/HYDRO_RST.2021-03-01_0000_DOMAIN1"
# HYDRO RESTART subset file
subHydroReasratFile <- "/glade/work/mazrooei/jedi/ctest_jedi_workflow/site_09253000/Restart/HYDRO_RST.2021-03-01_00.nc"

# Full LAKEPARM.nc file
fullLakeFile <- "/glade/p/cisl/nwc/nwmv21_finals/CONUS/DOMAIN_FinalParams/LAKEPARM_NWMv2.1.nc"
# Sub LAKEPARM.nc file
subLakeFile  <- ""



# Nudging file
#nudgeRestartFile <- "/glade/scratch/jamesmcc/NWM_v1.2_fix_eval/restarts/restart.2017053100/nudgingLastObs.2017-05-31_18:00:00.nc"

# Nudging subset file
#subNudgeRestartFile <- "/glade/scratch/arezoo/STEP/RESTART/nudgingLastObs.2017-05-31_18:00:00.nc_subset_June3"



#*****************************************************************************
# Reading the coordinate parameter text file.
#*****************************************************************************
coordsExport <- read.table(subCoordParamFile, header = TRUE)
geo_w <- coordsExport[which(coordsExport[,1] == "geo_sn"), "imin"]
geo_e <- coordsExport[which(coordsExport[,1] == "geo_sn"), "imax"]
geo_s <- coordsExport[which(coordsExport[,1] == "geo_sn"), "jmin"]
geo_n <- coordsExport[which(coordsExport[,1] == "geo_sn"), "jmax"]

hyd_w <- coordsExport[which(coordsExport[,1] == "hyd_sn"), "imin"]
hyd_e <-coordsExport[which(coordsExport[,1] == "hyd_sn"), "imax"] 
hyd_s <- coordsExport[which(coordsExport[,1] == "hyd_sn"), "jmin"]
hyd_n <- coordsExport[which(coordsExport[,1] == "hyd_sn"), "jmax"]

hyd_min <- coordsExport[which(coordsExport[,1] == "hyd_ns"), "jmin"]
hyd_max <- coordsExport[which(coordsExport[,1] == "hyd_ns"), "jmax"]

#*****************************************************************************
# subsetting the LSM RESTART file 
# #*****************************************************************************
 cmd <- paste0("ncks -O -d west_east,", geo_w-1, ",", geo_e-1, " -d south_north,", geo_s-1, ",", geo_n-1, " ", lsmRestartFile, " ", subLsmRestartFile)
 print(cmd); system(cmd)

#*****************************************************************************
# subset the hydro restart file 
#*****************************************************************************

# for the HYDRO restart files, some of the variables have the dimensions of the LSM and some HYDRO,
# therefore we need to define both the dimensions 

cmd <- paste0("ncks -O -d ix,", geo_w-1, ",", geo_e-1, " -d iy,",geo_s-1, ",", geo_n-1,
              " -d ixrt,", hyd_w-1, ",", hyd_e-1, " -d iyrt,",hyd_s-1,",",hyd_n-1," ",hydroReasratFile ," ", subHydroReasratFile)

print(cmd); system(cmd)

# read the list of all the links from the full extent Routlink file and the subsetted Routlink file
Rtlink <- rwrfhydro::ncdump(fullRtlinkFile, "link", quiet = TRUE)
subRtlink <- rwrfhydro::ncdump(subRtlinkFile, "link", quiet = TRUE)

# Find the indices for the subRoutlink file in the fullRulink file which will be used from subsetting the lines in the hydro restart file
subRtlinkInds <- which(Rtlink %in% subRtlink)

# get the list of all variables having dimension of link

ncin <- nc_open(subHydroReasratFile)
linkid <- plyr::llply(ncin$dim,'[[','id')$links
varList <- names(ncin$var)[plyr::laply(ncin$var, function(ll) any(ll$dimid == linkid))]
dataDf <- as.data.frame(matrix(nrow = nrow(subRtlink), ncol = length(varList), dimnames = list(NULL, as.list(varList))))

# read all the variables with link dim into memory, subset them to be ready for writing out
for (i in varList) {
  print(i)
  dataDf[,i] <- ncvar_get(ncin, i)[subRtlinkInds]
}

# first edit the dim variable "links"
cmdtxt <- paste0("ncks -O -d links,1,", nrow(subRtlink), " ", subHydroReasratFile," ", subHydroReasratFile)
print(cmdtxt)
system(cmdtxt)

# read all the variables with link as their dimension (only dimension) and subset the link dimension
ncin <- nc_open(paste0(subHydroReasratFile), write=TRUE)
for (i in varList) {
  print(i)
  data <- ncvar_get(ncin, i)
  ncvar_put(ncin, i, dataDf[,i])
}
nc_close(ncin)


# read the list of all the lakes from the full extent LAKEPARM.nc file and subsetted LAKEPARM.nc file

fullLake <- rwrfhydro::ncdump(fullLakeFile, "lake_id", quiet = TRUE)
if (file.exists(subLakeFile)){
    subLake <- rwrfhydro::ncdump(subLakeFile, "lake_id", quiet = TRUE)
    subLakeInds <- which(fullLake %in% subLake)

    # get the list of all variables having dimension of lakes
    ncin <- nc_open(subHydroReasratFile)
    linkid <- plyr::llply(ncin$dim,'[[','id')$lakes
    varList <- names(ncin$var)[plyr::laply(ncin$var, function(ll) any(ll$dimid == linkid))]
    dataDf <- as.data.frame(matrix(nrow = length(subLake), ncol = length(varList), dimnames = list(NULL, as.list(varList))))
    # read all the variables with lake dim into memory, subset them to be ready for writing out
    for (i in varList) {
      print(i)
      dataDf[,i] <- ncvar_get(ncin, i)[subLakeInds]
    }
    # first edit the dim variable "laks"
    cmdtxt <- paste0("ncks -O -d lakes,1,", length(subLake), " ", subHydroReasratFile," ", subHydroReasratFile)
    print(cmdtxt)
    system(cmdtxt)

    # read all the variables with lakes as their dimension (only dimension) and subset the lake dimension
    ncin <- nc_open(paste0(subHydroReasratFile), write=TRUE)
    for (i in varList) {
      print(i)
      data <- ncvar_get(ncin, i)
      ncvar_put(ncin, i, dataDf[,i])
    }
    nc_close(ncin)
                                           
} else {
    message('[Warning] File subsetted LAKEPARM.nc is not found, i.e., no lakes in the sub domain')
    cmdtxt <- paste0("ncks -O -x -v lakes,qlakei,qlakeo,resht ", subHydroReasratFile," ", subHydroReasratFile)
    print(cmdtxt)
    system(cmdtxt)
}


#*****************************************************************************
# subset the Nudging restart file
#*****************************************************************************
if (FALSE) {
# find the name of the gages that are in the file subset Routlink file

# read the list of gages from the subsetted Routlink
RtGages <- unique(rwrfhydro::ncdump(subRtlinkFile, "gages", quiet = TRUE))

# read the list of all gages from the nudging Full file
nudgeGages <- rwrfhydro::ncdump(nudgeRestartFile, "stationId", quiet = TRUE)

# Find the indices for which will be used from subsetting the lines in the hydro restart file
subRtlinkInds <- which(nudgeGages %in% RtGages)

# all the variables have the same dimension in this file
file.copy(nudgeRestartFile, subNudgeRestartFile)

# read the nudging file in, and subset them
nudgeInfo <- rwrfhydro::GetNcdfFile(subNudgeRestartFile, quiet=TRUE)
nudgeInfo$stationId <- nudgeInfo$stationId[subRtlinkInds]
nudgeInfo$time <- nudgeInfo$time[, subRtlinkInds]
nudgeInfo$discharge <- nudgeInfo$discharge[, subRtlinkInds]
nudgeInfo$model_discharge <- nudgeInfo$model_discharge[, subRtlinkInds]
nudgeInfo$discharge_quality <- nudgeInfo$discharge_quality[, subRtlinkInds]

# reduce the size of the file 
cmdtxt <- paste0("ncks -O -d stationIdInd,1,",  length(subRtlinkInds), " ", subNudgeRestartFile, " ", subNudgeRestartFile)
print(cmdtxt)
system(cmdtxt)

# read all the variables with link as their dimension (only dimension) and subset the link dimension
ncin <- nc_open(subNudgeRestartFile, write=TRUE)
for (i in names(nudgeInfo)) {
  print(i)
  data <- ncvar_get(ncin, i)
  ncvar_put(ncin, i, nudgeInfo[[i]])
}
nc_close(ncin)

}









