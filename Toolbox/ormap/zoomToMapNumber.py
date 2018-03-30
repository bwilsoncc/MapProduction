# -*- coding: utf-8 -*-
"""
Created on Tue Dec 19 15:43:00 2017
@author: Brian Wilson <bwilson@co.clatsop.or.us>
"""
from __future__ import print_function
import arcpy
from arcpy import mapping as MAP
import os, sys
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
import ORMAP_LayersConfig as ORMapLayers
import ORMAP_MapConfig as ORMapPageLayout
aprint(ORMapLayers.__file__)
aprint(ORMapPageLayout.__file__)
                           
from ormapnum import ormapnum
from cancellations import cancellations

mapindex_fields = [ "MapScale", "MapNumber", "OrMapNum", "SHAPE@", ]
MAPSCALE  = 0
MAPNUMBER = 1
ORMAPNUM  = 2
SHAPE     = 3
ROTATION  = 4   # need to reprocess data to get this...

cancelledfields  = [ "Taxlot", ]
TAXLOT = 0

pagelayoutfields = [ "MapAngle", ]
ANGLE = 0

can = cancellations(xlsfile = ORMapLayers.CancelledNumbersTable)

# ==============================================================================

def qqwhere(q, qq):
    """ Return a query string based on the quarter and quarterquarter letters 0ABCD """
    rval = "" # Nothing is highlighted
    if q != '0':
        if qq == '0':
            # Entire quarter is highlighted
            rval = q
        else:
            # One quarter quarter is highlighted
            rval = q + qq
    return rval

def set_main_definition_queries(mxd, df, orm, mapnumber, mapscale, query):
    """ Set definition queries for each layer in the MapView dataframe. 
        SET TO CONFIG TABLE VALUES. """

# NOTE "mapnumber" and "mapscale" can be used in config file
# so don't go removing them...
        
# So far, mapscale is not used in any queries... 
        
    arcpy.SetProgressorLabel("Set definition queries.")
    print("Using map config file; no optional DefCustomTable \"%s\"." % ORMapLayers.CUSTOMDEFINITIONQUERIES_TABLE)

    # Convert the layers into a dictionary
        
    d_layer = {}
    for (layername,pyexdq) in ORMapLayers.MainLayers:

        # evaluate expression to convert it from python to SQL
        dq=None
        if pyexdq:
            try:
                dq = eval(pyexdq)
            except Exception as e:
                print("An eval problem in python expression \"%s\"." % pyexdq, e)
                pass
            
        if dq:
            #print("dict: \"%s\" : \"%s\"" % (layername, dq))
            d_layer[layername] = dq

    # Now make one pass through the dataframe and actually fix up the definition queries.
        
    for lyr in MAP.ListLayers(mxd, "", df):
        if lyr.supports("DATASETNAME"):
            try:
                dq = d_layer[lyr.name]
                lyr.definitionQuery = dq
                print("New query on layer %s set to \"%s\"." % (lyr.longName, lyr.definitionQuery))
            except KeyError:
                if lyr.definitionQuery:
                    dq = '"' + lyr.definitionQuery + '"'
                    print("Query on layer \"%s\" is %s." % (lyr.longName, dq))
                    
        # I tested using "visible" attribute to turn on/off layers and it worked fine.
#        try:
#            s = d_anno[lyr.name]
#            lyr.visible = (mapscale == s)
#            aprint("%s %s %s" % (lyr.name, mapscale, s))
#        except KeyError:
#            pass

    return

def list_scalebars(mxd):
    sb = []
    # make a list of all the scalebar elements in the map.
    for elem in MAP.ListLayoutElements(mxd, "MAPSURROUND_ELEMENT"):
        if elem.name.lower().find("scalebar")>=0:
            sb.append(elem)
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
    
    sb = list_scalebars(mxd) # all the scalebars in the map
    try:
        sbname = ORMapPageLayout.Scalebars[mapscale] # the one we want
    except KeyError:
        # better to fail quietly than to up and quit
        sbname = ORMapPageLayout.DefaultScalebar # a substitute
        aprint("No scalebar found for %d so I am using %s instead." % (mapscale, sbname))
    visible_sb = selected_sb = None
    for elem in sb:
        # Is this scalebar visible?
        if on_page(elem, mxd):
            print("%s is visible." % elem.name)
            visible_sb = elem
            
            if sbname == elem.name:
            # "elem" is the scalebar we want
                #aprint("Current scalebar works for me.")
                # it's on the map, stop
                return
        else:
            if sbname == elem.name:
                selected_sb = elem
            
    if visible_sb:
        # Move this one off the map
        visible_sb.elementPositionX = selected_sb.elementPositionX
        visible_sb.elementPositionY = selected_sb.elementPositionY
        #aprint("I will hide %s over here (%d,%d)" % (visible_sb.name, visible_sb.elementPositionX, visible_sb.elementPositionY))
        pass
    if selected_sb:
        selected_sb.elementPositionX = ORMapPageLayout.ScalebarXY[0]
        selected_sb.elementPositionY = ORMapPageLayout.ScalebarXY[1]
        #aprint("and put %s on the page (%d,%d)" % (selected_sb.name, selected_sb.elementPositionX, selected_sb.elementPositionY))
    else:
        eprint("I did not find a good scalebar for this layout.")
        return
                
    return

def update_locator_maps(mxd, orm):
    """ Update the locator maps to emphasize the area of interest.

    mxd = map document
    orm = ormap object, used in query definitions

    You can either create a mask or a highlighter based on queries in the configuration.
    Set up query definitions in each dataframe to control this. """

    arcpy.SetProgressorLabel("Update locator maps")

    for dfname,layers,extlayername,scale,fcount in [
            (ORMapLayers.LocatorDF,  ORMapLayers.LocatorLayers,  ORMapLayers.LocatorExtentLayer,  ORMapLayers.LocatorScale,  ORMapLayers.LocatorFeatureCount),
            (ORMapLayers.SectionDF,  ORMapLayers.SectionLayers,  ORMapLayers.SectionExtentLayer,  ORMapLayers.SectionScale,  ORMapLayers.SectionFeatureCount),
            (ORMapLayers.QSectionDF, ORMapLayers.QSectionLayers, ORMapLayers.QSectionExtentLayer, ORMapLayers.QSectionScale, ORMapLayers.QSectionFeatureCount),
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

            #arcpy.RefreshActiveView()

            # Now's our chance to hide (or show) locator maps!!
            # We do this by making layers visible or not if there are any features in the featuecount layer
            # after setting the query
            visibility = True
            try:
                fc_layer = GetLayer(mxd,df,fcount)
                c = int(arcpy.GetCount_management(fc_layer).getOutput(0))
                #aprint("count = %d" % c)
                if c == 0:
                    visibility = False
                    aprint("Nothing to see in layer \"%s\"." % extlayername)
            except Exception as e:
                aprint("Error in %s, %s" % (extlayername, e))

            for l in MAP.ListLayers(mxd,"*",df):
                l.visible = visibility
                #aprint("%s %s" % (l.name, l.visible))

    return

def update_page_elements(mxd, df, orm):

    arcpy.SetProgressorLabel("Set up page layout elements")
    
    #aprint("Attendez! Scale is now %s" % df.scale)
    select_scalebar(mxd, df.scale)
  
    for elm in MAP.ListLayoutElements(mxd):
        if elm.name == "PlotDate":
            now = datetime.now()
            elm.text = "PLOT DATE: %2d/%02d/%4d" % (now.month, now.day, now.year)
        
        elif elm.name == ORMapPageLayout.CancelledTaxlotsElement:
            cancelledtaxlot_count = populate_cancelled_taxlot_table(mxd, orm.dotted)
            offset = 0
            if cancelledtaxlot_count == 0:
                # Move the cancelled taxlot table off the layout
                offset = 4
            elm.elementPositionX = ORMapPageLayout.CancelledTaxlotsXY[0] + offset
            elm.elementPositionY = ORMapPageLayout.CancelledTaxlotsXY[1]
            
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

def populate_cancelled_taxlot_table(mxd, dotted):
    """ Fill in the cancelled taxlot table in the page. 
        Return the number of cancelled taxlots. """

    aprint("populate_cancelled_taxlot_table(mxd,\"%s\")" % dotted)        
    arcpy.SetProgressorLabel("Populating cancelled taxlot table")
        
    # Note that this function is not affected by any query definition.
    cancelled_taxlots = can.get_list(dotted)
    ncols = len(ORMapPageLayout.CancelledNumbersColumns)
    cancelled_elem = []

    # Empty out the text boxes

    for x in xrange(0, ncols):
        try:
            cancelled_elem.append(None)
            cancelled_elem[x] = MAP.ListLayoutElements(mxd, "TEXT_ELEMENT", ORMapPageLayout.CancelledNumbersColumns[x])[0]
            cancelled_elem[x].text = " " # This element has some text in it (event just a single space) so ArcMap does not "lose" it.
        except Exception as e:
            aprint("Exception \"e\" when initializing cancelled column %d" % (e,x))
            pass

    if len(cancelled_taxlots): 
        aprint("Loading %d cancelled taxlots." % len(cancelled_taxlots))
        
        # Sort out the data into as ;ost pf columns
        max_y, columns = make_table(cancelled_taxlots, ncols)

        # Adjust the font size of the table according to the number of rows
        fontsize = 10
        maxrows = ORMapPageLayout.MaxCancelledRows
        if max_y > maxrows: fontsize = 8

        x = 0
        for column in columns:
            cancelled_elem[x].text = column
            cancelled_elem[x].fontSize = fontsize
            x += 1
        
    return len(cancelled_taxlots)

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
    update_locator_maps(mxd, orm)

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
    #select_scalebar(mxd, 24000)
    test_layouts(mxd)
    del mxd

    print("Tests completed.")
# That's all
