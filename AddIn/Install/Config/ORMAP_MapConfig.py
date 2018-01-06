# ---------------------------------------------------------------------------
# Description: This is a configuration file specifically for 18 x 24 inch maps

# Cancelled Taxlot Numbers appear in a table with the numbers sorted
# vertically. The elements in the table are a title and several columns.
#
# Note if you "ungroup" the elements in arcmap and then regroup them
# you will have to reset the name on the group.

# I move the group off the page to hide it, 
# so I have to know where it should go to show it.
CancelledTaxlotsElement = "can_group"
CancelledTaxlotsXY = (22.17, 7.2) # anchor point center top

# Each of these is a text block in the layout
CancelledNumbersColumns = ("can1", "can2", "can3", "can4")

MaxCancelledRows = 100


# There are 3 locator maps, and I move them off the layout to hide them
# if they are not useful at the current map scale. 

# When moving the locators back ONTO the page layout I have to have XY's

#LocatorXY = ()
LocatorSectionXY  = (20.45, 10.7081)
LocatorQSectionXY = (20.4509, 7.974)

# ---------------------------------------------------------------------------
# Old stuff that probably gets ignored.

DataFrameMinX= 0.4
DataFrameMinY= 0.5
DataFrameMaxX= 19.9 + DataFrameMinX
DataFrameMaxY= 17.5 + DataFrameMinY

TitleX=10.5
TitleY=17.8411

DisclaimerX=2.5684
DisclaimerY=17.8128

URCornerNumX=20.2
URCornerNumY=18.0009

LRCornerNumX=20.2
LRCornerNumY=1.3113

ScaleBarXY = (20.6255, 16.8447)
Scalebars = {  240:"Scalebar240",   #   50 ft
               480:"Scalebar240",   #  100 ft
               600:"Scalebar600",   #  100 ft
               720:"Scalebar600",   #  120 ft
              1200:"Scalebar600",   #  200 ft
              2400:"Scalebar4800",  #  500 ft
              4800:"Scalebar4800",  # 1000 ft
             24000:"Scalebar24000", # This one shows 1 mile
             }

DateX=1.6711
DateY=17.3485

NorthX=0
NorthY=0

MapAngle=0

# CONTROL DISTANCE BETWEEN MAPTITLE AND MAPSCALE VALUE
MapScaleDist=0.15

