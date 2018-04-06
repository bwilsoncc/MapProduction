# -*- coding: utf-8 -*-
"""
Created on Tue Dec 19 15:43:00 2017
@author: Brian Wilson <bwilson@co.clatsop.or.us>
"""
from __future__ import print_function
import arcpy
from arcpy import mapping as MAP
import os, sys, re
from datetime import datetime
from arc_utilities import aprint, eprint, SetDefinitionQuery, GetDataframe, GetLayer

# =============================================================================
# Load the "configuration files"
# NB, force string into lower case to make sure it works in Windows
configpath = os.path.dirname(__file__)
if not configpath: configpath = os.getcwd()
configpath=os.path.normcase(configpath).replace("ormap","")
print("__file__=%s configpath=%s" % (__file__, configpath))
sys.path.append(configpath)
import ORMAP_config as ORMAP
aprint(ORMAP.__file__)
                           
from ormapnum import ormapnum
from cancellations import cancellations

# preload spreadsheet
can = cancellations(xlsfile = ORMAP.CancelledNumbersTable)

# locations of locator maps and cancelled taxlots group when on the page.
locator_positions = {} # tuples index by df name
can_x = can_y = 0

# ==============================================================================

def make_scalebar_dict(mxd):
    sb = {}
    # make a list of all the scalebar elements in the map.
    for elem in MAP.ListLayoutElements(mxd, "MAPSURROUND_ELEMENT"):
        name = elem.name.lower()
        if name.find("scalebar") >= 0:
            sb[name] = elem
    return sb

def on_page(elem, mxd):
    """ Return TRUE if the element is visible on its page layout. """
    x = elem.elementPositionX
    y = elem.elementPositionY
        
    minx = -elem.elementWidth
    miny = -elem.elementHeight
    maxx = mxd.pageSize.width
    maxy = mxd.pageSize.height
    
    #print(elem.name,(x,y),(minx,miny),(maxx,maxy))
    
    return (x > minx and x < maxx) and (y > miny and y <= maxy)

def select_scalebar(mxd, mapscale):
    
    sb = make_scalebar_dict(mxd) # all the scalebars in the map
    sbname = "scalebar%d" % mapscale # the one we want
    if not sb.has_key(sbname):
        sbname = "scalebardefault"
        if not sb.has_key(sbname):
            aprint("There is no default scalebar.")
            return
        aprint("No scalebar found for %d so I am using %s." % (mapscale, sbname))

    visible_sb = new_sb = None
    for name in sb:
        elem = sb[name]
        lcname = elem.name.lower()

        # Is this scalebar visible?
        if on_page(elem, mxd):
            visible_sb = elem           
            if sbname == lcname:
                #aprint("%s is already visible." % sbname)
                # it's already on the map, stop
                return
        else:
            if sbname == lcname:
                new_sb = elem
   
    if not visible_sb:
        aprint("There is no scalebar visible on the page. Position one on the map so I know where it belongs.")
        return

    map_x = visible_sb.elementPositionX
    map_y = visible_sb.elementPositionY        

    # Move this one off the map
    visible_sb.elementPositionX = new_sb.elementPositionX
    visible_sb.elementPositionY = new_sb.elementPositionY
    #aprint("I will hide %s over here (%d,%d)" % (visible_sb.name, visible_sb.elementPositionX, visible_sb.elementPositionY))

    if new_sb:
        new_sb.elementPositionX = map_x
        new_sb.elementPositionY = map_y
        aprint("Put %s on the page (%d,%d)" % (new_sb.name, new_sb.elementPositionX, new_sb.elementPositionY))
    else:
        aprint("I did not find a good scalebar for this layout.")
                
    return

def update_locator_maps(mxd, orm):
    """ Update the locator maps to emphasize the area of interest.
    mxd = map document
    orm = ormap object, used in query definitions

    You can either create a mask or a highlighter based on queries in the configuration.
    Set up query definitions in each dataframe to control this. 
    
    Returns the (x,y) location for the next stacked layout element. """

    global sections_x, sections_y, qsections_x, qsections_y

    # We're trying a stacked layout here. The county-wide locator will be at the top,
    # and successive features will be below at suitable spacings.

    x = y = 0

    for dfname,layers,extlayername,scale,fcount in [
            (ORMAP.LocatorDF,  ORMAP.LocatorLayers,  ORMAP.LocatorExtentLayer,  ORMAP.LocatorScale,  ORMAP.LocatorFeatureCount),
            (ORMAP.SectionDF,  ORMAP.SectionLayers,  ORMAP.SectionExtentLayer,  ORMAP.SectionScale,  ORMAP.SectionFeatureCount),
            (ORMAP.QSectionDF, ORMAP.QSectionLayers, ORMAP.QSectionExtentLayer, ORMAP.QSectionScale, ORMAP.QSectionFeatureCount),
            ]:
        df = GetDataframe(mxd, dfname)

        # Set query definitions

        for layername, qd in layers:
            query = ""
            #aprint('qd = %s' % qd)
            if qd:
                try:
                    query = eval(qd)
                except Exception as e:
                    aprint("EVAL failed: query=\"%s\", %s" % (query, e))
            SetDefinitionQuery(mxd, df, layername, query) 

        # Set extent (pan and zoom as needed)
        # and possibly hide the locator map

        if extlayername:
            # Pan and zoom are optional in locator maps.
            ext_layer = GetLayer(mxd, df, extlayername)
            df.extent = ext_layer.getExtent()
            # if a fixed scale is specified in config, use it
            if scale: df.scale  = scale

        # Now's our chance to hide (or show) locator maps!!

        visibility = True
        try:
            fc_layer = GetLayer(mxd,df,fcount)
            c = int(arcpy.GetCount_management(fc_layer).getOutput(0))
            if c == 0:
                visibility = False
                aprint("Nothing to see in layer \"%s\"." % extlayername)
        except Exception as e:
            aprint("Error in %s, %s" % (extlayername, e))

        elm = None
        try:
            elm = MAP.ListLayoutElements(mxd, "DATAFRAME_ELEMENT", dfname)[0]
        except IndexError:
            pass

        if elm:
                # leftover from before stacking was implemented
#                if on_page(elm, mxd):
#                    # this element is on the page so save its location for future use
#                    locator_positions[elm.name] = (elm.elementPositionX, elm.elementPositionY)
#                x=y=0
#                try:
#                    x = locator_positions[elm.name][0]
#                    y = locator_positions[elm.name][1]
#                except:
#                    aprint("Can't figure out where to put \"%s\"" % elm.name)

            if x <> 0 and y <> 0:
                # LocatorDF won't get moved because it's always visible
                elm.elementPositionX = x
                elm.elementPositionY = y

            if not visibility:
                elm.elementPositionX = mxd.pageSize.width + 2
                elm.elementPositionY = y

            if on_page(elm, mxd):
                # Set position for the next element below this one
                x = elm.elementPositionX
                y = elm.elementPositionY - (elm.elementHeight + .15)

    return (x,y)


def update_page_elements(mxd, df, orm):
    #aprint("Setting up page layout")
   
    select_scalebar(mxd, df.scale)
  
    try:
        elm = MAP.ListLayoutElements(mxd, "TEXT_ELEMENT", "PlotDate")[0]
        now = datetime.now()
        elm.text = "PLOT DATE: %2d/%02d/%4d" % (now.month, now.day, now.year)
    except IndexError:
        aprint("Could not find a PlotDate text element. Skipping.")

    return

def update_cancelled(mxd, orm, x,y):
    global can_x, can_y

    can_elm = None
    try:
        can_elm = MAP.ListLayoutElements(mxd, "GRAPHIC_ELEMENT", "can*")[0]
    except IndexError:
        aprint("Could not find a cancelled taxlots group element. Skipping.")
        return

#    if on_page(can_elm,mxd):
#        can_x = can_elm.elementPositionX
#        can_y = can_elm.elementPositionY
#    elif can_x == 0 and can_y == 0:
#        aprint("The cancelled taxlots element \"%s\" is not on the map so it will never print." % can_elm.name)

    cancelled_taxlots = can.get_list(orm.dotted)
    aprint("Cancelled taxlots: %d" % len(cancelled_taxlots))
    if len(cancelled_taxlots) == 0:
        # Move the cancelled taxlot table off the layout
        can_elm.elementPositionX = mxd.pageSize.width + 3
        can_elm.elementPositionY = y
    else:
        can_elm.elementPositionX = x
        can_elm.elementPositionY = y

    populate_cancelled_taxlot_table(mxd, cancelled_taxlots)
            
    return

def make_table(seq, columns):
    """ Break the sequence into 'n' columns and return them. """
    table = ""
    maxy = (len(seq)+columns-1)/columns
    i = 0
    columns = []
    for item in seq:
        table += str(item).ljust(6) + "\n"
        i += 1
        if not i % maxy:
            columns.append(table)
            table = ""
    if table:
        columns.append(table)

    return maxy,columns

def populate_cancelled_taxlot_table(mxd, taxlots):
    """ Fill in the cancelled taxlot table in the page. 
        Return the number of cancelled taxlots. """

    #aprint("Populating cancelled taxlot table")
        
    # Count the can* columns in this MXD and empty them out.

    ncols = 0
    cols = []
    for elm in MAP.ListLayoutElements(mxd, "TEXT_ELEMENT", "can*"):
        if re.search('^can\d+$', elm.name):
            cols.append(elm)
            ncols += 1
            elm.text = " " # This element has some text in it (event just a single space) so ArcMap does not "lose" it.
    
    if len(taxlots):
        # Sort out the data into as a list of columns
        max_y, columns = make_table(taxlots, ncols)

        # Adjust the font size of the table according to the number of rows
        fontsize = 10
        if max_y > ORMAP.MaxCancelledRows: fontsize = 8

        x = 0
        for column in columns:
            cols[x].text = column
            cols[x].fontSize = fontsize
            x += 1
        
    return

# ==============================================================================

def update_page_layout(mxd, pagename):
    """Update the map document page layout using the given pagename."""
    
    try:
        maindf = mxd.dataDrivenPages.dataFrame
        ddp_layer = mxd.dataDrivenPages.indexLayer
    except Exception as e:
        aprint(e)
        return

    page_id = mxd.dataDrivenPages.getPageIDFromName(pagename)
    mxd.dataDrivenPages.currentPageID = page_id
    
    orm = ormapnum()
    orm.expand(pagename)
    #aprint("%s -> %s -> %s" % (pagename, orm.dotted, orm.longmaptitle))

    update_page_elements(mxd, maindf, orm)
    (x,y) = update_locator_maps(mxd, orm)
    update_cancelled(mxd, orm, x,y)

    arcpy.RefreshActiveView()

    return

def test_layouts(mxd):
    for pagename in ["8 10 8BB", "8 10 5CD", "8 10 5CD D1", "8 10 5CD D2", ]:
        print("pagename: %s" % pagename)
        update_page_layout(mxd, pagename)
 
# ======================================================================

if __name__ == '__main__':
    try:
        # Try to run as a python script (from a toolbox in arcmap)
        mxdname="CURRENT"
        mapnumber=sys.argv[1]
    except IndexError:
        # Run in the debugger
        mxdname = "C:\\GeoModel\\Clatsop\\Workfolder\\TestMap.mxd"
    
    mxd = MAP.MapDocument(mxdname)
    select_scalebar(mxd, 120)
    select_scalebar(mxd, 240)
    select_scalebar(mxd, 1200)
    select_scalebar(mxd, 2400)
    select_scalebar(mxd, 4800)
    select_scalebar(mxd, 24000)
    test_layouts(mxd)
    del mxd

    print("Tests completed.")
# That's all
