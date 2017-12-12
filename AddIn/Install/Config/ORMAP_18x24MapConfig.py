# ---------------------------------------------------------------------------
# Ormap18x24MapConfig.py
# Created by: Shad Campbell
# Date: 3/11/2011
# Updated by: 
# Description: This is a configuration file specifically for 18 x 24 inch maps
# to be customized by each county Do not delete any of the items in this file.
# If they are not in use then specify thier value to 0.  
# ---------------------------------------------------------------------------

# Clatsop County
# 2017-12-11 -- Brian converted this file from GeoModel/Clatsop/MapProduction18x24.ini

DataFrameMinX= 0.4
DataFrameMinY= 0.5
DataFrameMaxX= 19.9 + DataFrameMinX
DataFrameMaxY= 17.5 + DataFrameMinY
TitleX=10.5
TitleY=17.8411
DisclaimerX=2.5684
DisclaimerY=17.8128
CancelNumX=20.3418
CancelNumY=16.5706
URCornerNumX=20.2
URCornerNumY=18.0009
LRCornerNumX=20.2
LRCornerNumY=1.3113
ScaleBarX=10.1606
ScaleBarY=17.008
DateX=1.6711
DateY=17.3485
NorthX=0
NorthY=0
MapAngle=0

CountyName='Clatsop County, Oregon'
MaxCancelledRows = 100
CancelledSortField='OBJECTID'
CancelledNumberPrefix='Cancelled Nos.'

;CONTROL DISTANCE BETWEEN MAPTITLE AND COUNTY NAME
CountyNameDist=-0.25

;CONTROL DISTANCE BETWEEN MAPTITLE AND MAPSCALE VALUE
MapScaleDist=0.15
