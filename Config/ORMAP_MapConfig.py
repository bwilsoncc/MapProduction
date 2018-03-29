# ---------------------------------------------------------------------------
# Cancelled Taxlot Numbers appear in a table with the numbers sorted
# vertically. The elements in the table are a title and several columns.
#
# Note if you "ungroup" the elements in arcmap and then regroup them
# you will have to reset the name on the group.

# I move the group off the page to hide it, 
# so I have to know where it should go to show it.
CancelledTaxlotsElement = "can_group"
CancelledTaxlotsXY = (22.1, 7.8) # this assumes anchor point center top

# Each of these is a text block in the layout
CancelledNumbersColumns = ("can1", "can2", "can3", "can4", "can5")

MaxCancelledRows = 15 # Go to 8 point font if # of rows exceeds this

ScalebarXY = (22.2, 16.7)
Scalebars = {  240:"Scalebar240",   #   50 ft
               360:"Scalebar240",   #   80 ft
               480:"Scalebar240",   #  100 ft
               600:"Scalebar600",   #  100 ft
               720:"Scalebar4800",  #  150 ft
              1200:"Scalebar600",   #  200 ft
              2400:"Scalebar4800",  #  500 ft
              4800:"Scalebar4800",  # 1000 ft
             24000:"Scalebar24000", # This one shows 1 mile
             }
# use this if nothing else matches
DefaultScalebar = Scalebars[600] 

MapAngle=0

