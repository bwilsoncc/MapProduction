# -*- coding: utf-8 -*-
"""
Created on Tue Dec 19 15:43:00 2017

@author: bwilson
"""
from __future__ import print_function
import arcpy
from arcpy import mapping as MAP
#import pythonaddins
import os, sys
import datetime
from ormap_utilities import ORMapLayers, ORMapPageLayout, aprint, eprint, \
                            get_dataframe, get_layer, set_definition_query
from ormapnum import ormapnum
from cancellations import read_cancelled, make_table

mapindex_fields = [ "MapScale", "MapNumber", "CityName", "OrMapNum", "SHAPE@", ]
MAPSCALE  = 0
MAPNUMBER = 1
CITYNAME  = 2
ORMAPNUM  = 3
SHAPE     = 4

cancelledfields = [ "Taxlot", ]
TAXLOT = 0

pagelayoutfields = [ "MapAngle", ]
ANGLE = 0

# ==============================================================================


def readtable(mxd, df, tablename, fields, whereclause):
    """ Read a table of values to be displayed as cancelled taxlot numbers. """
    tableview = row = None
    table = []
    try:
        tableview = MAP.ListTableViews(mxd, tablename, df)[0]
    except IndexError:
        #aprint("table=\"%s\" query=\"%s\"" % (tablename, whereclause))
        return table

    with arcpy.da.SearchCursor(tableview, fields, whereclause) as cursor:
        try:
            for row in cursor:
                table.append(row)
        except Exception as e:
            #eprint("Cant read, %s" % e)
            pass
    return table

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

def get_mapnumber_query(mapnumber):
    """ Convert a mapnumber (possibly with a wildcard in it) into a SQL query. """
    
    # I have to use different delimiters for different databases. Sigh.
    mapnumber_field = ORMapLayers.MapNumberField
    delimiter_l = '['
    delimiter_r = ']'
    #wildcard    = '*'
    return "%s%s%s LIKE '%s'" % (delimiter_l, mapnumber_field, delimiter_r, mapnumber)

def set_main_definition_queries(mxd, df, mapnumber, mapscale, query):
    """ Set definition queries for each layer in the main dataframe. 
        SEARCH FOR AN ITEM IN THE DEF QUERY TABLE FIRST... 
        OTHERWISE SET TO CONFIG TABLE VALUES. """

# So far, mapscale is not used in any queries... 
        
    aprint("Setting up main layer definition queries.")
    table_defquery = readtable(mxd, df, ORMapLayers.CUSTOMDEFINITIONQUERIES_TABLE, "*", query)
    if len(table_defquery):
        
        """ I've never tested this code!!! """
        
        #-- Items stored in long string input defQueryString field.  Pull them out and into their own array.
        defQueryList = table_defquery.defQueryString.split(";")
        
        d_query = {}
        for defQueryItem in defQueryList:
            lyr,qry = defQueryItem.split(":")
            d_query[lyr] = qry
            
        for lyr in MAP.ListLayers(mxd, "", df):
            if lyr.supports("DATASETNAME"):
                try:
                    lyr.definitionQuery = d_query[lyr.name]
                except KeyError:
                    pass

    else:
        aprint("Using map config file; no optional DefCustomTable \"%s\"." % ORMapLayers.CUSTOMDEFINITIONQUERIES_TABLE)
        # Define all the layername, query definition pairs as a list of tuples.
        # Add on the "EXTRA" layers (20 of them)
        # Then evaluate (using "eval()" each expression so that the script does not choke
        # if a layer is not defined in the config file.
        l_layers = [
                    ("LOTSANNO_LAYER", "ORMapLayers.LOTSANNO_QD"),
                    ("PLATSANNO_LAYER", "PLATSANNO_QD"),
                    ("TAXCODEANNO_LAYER", "TAXCODEANNO_QD"),
                    ("TAXNUMANNO_LAYER", "TAXNUMANNO_QD"),
                    ("ACRESANNO_LAYER", "ACRESANNO_QD"),
                    ("ANNO10_LAYER", "ANNO10_QD"),
                    ("ANNO20_LAYER", "ANNO20_QD"),
                    ("ANNO30_LAYER", "ANNO30_QD"),
                    ("ANNO40_LAYER", "ANNO40_QD"),
                    ("ANNO50_LAYER", "ANNO50_QD"),
                    ("ANNO60_LAYER", "ANNO60_QD"),
                    ("ANNO100_LAYER", "ANNO100_QD"),
                    ("ANNO200_LAYER", "ANNO200_QD"),
                    ("ANNO400_LAYER", "ANNO400_QD"),
                    ("ANNO800_LAYER", "ANNO800_QD"),
                    ("ANNO2000_LAYER", "ANNO2000_QD"),
                    ("CORNER_ABOVE_LAYER", "CORNER_ABOVE_QD"),
                    ("TAXCODELINES_ABOVE_LAYER", "TAXCODELINES_ABOVE_QD"),
                    ("TAXLOTLINES_ABOVE_LAYER", "TAXLOTLINES_ABOVE_QD"),
                    ("REFLINES_ABOVE_LAYER", "REFLINES_ABOVE_QD"),
                    ("CARTOLINES_ABOVE_LAYER", "CARTOLINES_ABOVE_QD"),
                    ("WATERLINES_ABOVE_LAYER", "WATERLINES_ABOVE_QD"),
                    ("WATER_ABOVE_LAYER", "WATER_ABOVE_QD"),
                    ("MAPINDEXSEEMAP_LAYER", "MAPINDEXSEEMAP_QD"),
                    ("MAPINDEX_LAYER", "MAPINDEX_QD"),
                    ("CORNER_BELOW_LAYER", "CORNER_BELOW_QD"),
                    ("TAXCODELINES_BELOW_LAYER", "TAXCODELINES_BELOW_QD"),
                    ("TAXLOTLINES_BELOW_LAYER", "TAXLOTLINES_BELOW_QD"),
                    ("REFLINES_BELOW_LAYER", "REFLINES_BELOW_QD"),
                    ("CARTOLINES_BELOW_LAYER", "CARTOLINES_BELOW_QD"),
                    ("WATERLINES_BELOW_LAYER", "WATERLINES_BELOW_QD"),
                    ("WATER_BELOW_LAYER", "WATER_BELOW_QD"),
                    ]
        for extra in range(1,20):
            l_layers.append(("EXTRA%d_LAYER" % extra,"EXTRA%d_QD" % extra))

        default_q = ORMapLayers.DEFAULT_QD

        # Convert the layers into a dictionary
        
        d_layer = {}
        for (v_lyrname,v_dq) in l_layers:
            try:
                layername = eval("ORMapLayers."+v_lyrname)
            except AttributeError:
                aprint("Layer not found \"%s\"; ignoring it." % v_lyrname)
                continue
            try:
                dq = eval("ORMapLayers."+v_dq)
            except AttributeError:
                aprint("Query not found \"%s\"; using default." % v_dq)
                dq = default_q
            #print(layername, dq)
            d_layer[layername] = dq.replace("*MapNumber*", mapnumber).replace("*MapScale*", str(mapscale))                    

        # Now make one pass through the dataframe and actually fix up the definition queries.

        for lyr in MAP.ListLayers(mxd, "", df):
            if lyr.supports("DATASETNAME"):
                try:
                    lyr.definitionQuery = d_layer[lyr.name]
                    print("layername: %s query: \"%s\"" % (lyr.name, lyr.definitionQuery))
                except KeyError:
                    print("No need to change layer \"%s\"." % lyr.name)
        return

def adjust_masking(mxd, maindf, orm, mapnumber):
    """ Some of the layers in our current test map are 
    "masks" (show everything but the selection)
    and some are "highlighters" (show selected polygon(s)). 
    Set up query definitions in each dataframe to control this. """

    # Try to read each dataframe name from config
    # and fall back to a default name.
    
    try:
        locatordf_name = ORMapLayers.LocatorDF
    except AttributeError:
        locatordf_name = "LocatorDF"    
    locatordf   = get_dataframe(mxd, locatordf_name)

    try:
        sectionsdf_name = ORMapLayers.SectionsDF
    except AttributeError:
        sectionsdf_name = "SectionsDF"    
    sectionsdf  = get_dataframe(mxd, sectionsdf_name)

    try:
        qsectionsdf_name = ORMapLayers.QSectionsDF
    except AttributeError:
        qsectionsdf_name = "QSectionsDF"
    qsectionsdf = get_dataframe(mxd, qsectionsdf_name)

    # Set up the definition query on each data frame layer to highlight polygons.

    query = ""
    if mapnumber: query = ORMapLayers.MAPINDEXMASK_QD % mapnumber 
    set_definition_query(mxd, maindf, ORMapLayers.MAPINDEXMASK_LAYER, query)

    query = ""
    if mapnumber: query = ORMapLayers.LOCATOR_QD % (int(orm.township), int(orm.range), orm.range_dir) 
    set_definition_query(mxd, locatordf, ORMapLayers.LOCATOR_LAYER, query)

    query = ""
    if orm.section: query = ORMapLayers.SECTIONS_QD % orm.section
    set_definition_query(mxd, sectionsdf, ORMapLayers.SECTIONS_LAYER, query)
        
    query = ORMapLayers.QSECTIONS_QD % qqwhere(orm.quarter, orm.quarterquarter)
    set_definition_query(mxd, qsectionsdf, ORMapLayers.QTRSECTIONS_LAYER, query)

    return

def build_titles(orm, s_mapscale, s_cityname):
    """ Build text strings usable for short and long titles and scale text.
    Return them as a tuple. """
    
    shortmaptitle = ('%s.%s.%s' % (orm.township, orm.range, orm.section)).rstrip('.')
    if orm.quarter != '0':
        shortmaptitle += orm.quarter
        if orm.quarterquarter != '0': shortmaptitle += orm.quarterquarter
    if s_cityname.strip():
        shortmaptitle += "\n" + s_cityname.replace(",","\n")

    townrng = "T" + str(orm.township) + orm.township_frac + orm.township_dir + ' ' + \
         "R" + str(orm.range)    + orm.range_frac    + orm.range_dir    + " WM"
    section_text = orm.qqtext()
    scale_text   = "1\" = %d'" % (int(s_mapscale) / 12)

    if s_mapscale == "24000":
        longmaptitle = townrng
    elif s_mapscale == "4800":
        longmaptitle = "SECTION " + str(orm.section) + " " + townrng    
    else:
        longmaptitle = section_text + " SEC." + str(orm.section) + " " + townrng
                 
        if str(section_text)=="":
            longmaptitle = "SECTION " + str(orm.section) + " " + townrng
        if str(orm.section)=="":
            longmaptitle = townrng

    #MODIFY TITLE FOR NON-STANDARD MAPS
    if orm.maptype == "S":
        longmaptitle = "SUPPLEMENTAL MAP NO. %d\n" % orm.mapnumber + longmaptitle
    elif orm.maptype == "D":
        longmaptitle = "DETAIL MAP NO. %d\n" % orm.mapnumber + longmaptitle
    elif orm.maptype == "T":
        longmaptitle = "SHEET NO. %d\n" % orm.mapnumber + longmaptitle

    print(shortmaptitle, longmaptitle, scale_text)
    return shortmaptitle, longmaptitle, scale_text

def update_page_elements(mxd, df, orm, mapnumber_query, s_mapnum, s_mapscale, s_cityname):
    
    # Allowing changes to the page elements based on settings here
    # would allow a custom set up for each map page, by loading settings
    # from a table.

    # Using a table has the advantage of allowing a custom set up for each page.
    table = readtable(mxd, df, ORMapLayers.PAGELAYOUT_TABLE, pagelayoutfields, mapnumber_query)
    if not len(table):
        # Use configuration - one set up for every map page.
        aprint("Using configuration file for page layout; no PageLayoutTable found. \"%s\". Query: %s" % (ORMapLayers.PAGELAYOUT_TABLE, mapnumber_query))

        dataframe_minx = ORMapPageLayout.DataFrameMinX
        dataframe_miny = ORMapPageLayout.DataFrameMinY
        dataframe_maxx = ORMapPageLayout.DataFrameMaxX
        dataframe_maxy = ORMapPageLayout.DataFrameMaxY
        #df.extent = extent
        df.rotation = ORMapPageLayout.MapAngle
        
#        TitleX = ORMapPageLayout.TitleX
#        TitleY = ORMapPageLayout.TitleY

#        DisclaimerX = ORMapPageLayout.DisclaimerX
#        DisclaimerY = ORMapPageLayout.DisclaimerY

#        CancelNumX = ORMapPageLayout.CancelNumX
#        CancelNumY = ORMapPageLayout.CancelNumY

#        DateX = ORMapPageLayout.DateX
#        DateY = ORMapPageLayout.DateY

#        URCornerNumX = ORMapPageLayout.URCornerNumX
#        URCornerNumY = ORMapPageLayout.URCornerNumY
#        LRCornerNumX = ORMapPageLayout.LRCornerNumX
#        LRCornerNumY = ORMapPageLayout.LRCornerNumY

#        ScaleBarX = ORMapPageLayout.ScaleBarX
#        ScaleBarY = ORMapPageLayout.ScaleBarY

#        NorthX = ORMapPageLayout.NorthX
#        NorthY = ORMapPageLayout.NorthY

    else:
        # Use page layout table
        
#        dataframe_minx = pagelayoutrow.DataFrameMinX
#        dataframe_miny = pagelayoutrow.DataFrameMinY
#        dataframe_maxx = pagelayoutrow.DataFrameMaxX
#        dataframe_maxy = pagelayoutrow.DataFrameMaxY

#        MapPositionX = pagelayoutrow.MapPositionX
#        MapPositionY = pagelayoutrow.MapPositionY
        
#        mapExtent = arcpy.Extent(MapPositionX-1, MapPositionY-1, MapPositionX+1, MapPositionY+1)

#        MapAngle = pagelayoutrow.MapAngle
        df.rotation = table[0][ANGLE]

#        TitleX = pagelayoutrow.TitleX
#        TitleY = pagelayoutrow.TitleY
#        DisclaimerX = pagelayoutrow.DisclaimerX
#        DisclaimerY = pagelayoutrow.DisclaimerY
#        CancelNumX = pagelayoutrow.CancelNumX
#        CancelNumY = pagelayoutrow.CancelNumY
#        DateX = pagelayoutrow.DateX
#        DateY = pagelayoutrow.DateY
#        URCornerNumX = pagelayoutrow.URCornerNumX
#        URCornerNumY = pagelayoutrow.URCornerNumY
#        LRCornerNumX = pagelayoutrow.LRCornerNumX
#        LRCornerNumY = pagelayoutrow.LRCornerNumY
#        ScaleBarX = pagelayoutrow.ScaleBarX
#        ScaleBarY = pagelayoutrow.ScaleBarY
#        NorthX = pagelayoutrow.NorthX
#        NorthY = pagelayoutrow.NorthY

    #MISC Relative Map Distances
#    CountyNameDist = ORMapPageLayout.CountyNameDist
#    MapScaleDist = ORMapPageLayout.MapScaleDist

    
    (shorttitle, longtitle, scale_text) = build_titles(orm, s_mapscale, s_cityname)
    
    for elm in MAP.ListLayoutElements(mxd):
        #TEXT ELEMENTS
        if elm.name=="MapNumber":
            elm.text = s_mapnum
        
        elif elm.name.lower() == "mainmaptitle":
            elm.text = longtitle
            #elm.elementPositionX = TitleX
            #elm.elementPositionY = TitleY
        
        elif elm.name.lower() == "smallmaptitle":
            elm.text = longtitle
                        
        elif elm.name == "MainMapScale":
            elm.text = scale_text
#            elm.elementPositionX = TitleX
#            elm.elementPositionY = TitleY - MapScaleDist

        elif elm.name == "UpperLeftMapNum":
            elm.text = shorttitle

        elif elm.name == "UpperRightMapNum":
            elm.text = shorttitle
            #elm.elementPositionX = URCornerNumX
            #elm.elementPositionY = URCornerNumY

        elif elm.name == "LowerLeftMapNum":
            elm.text = shorttitle

        elif elm.name == "LowerRightMapNum":
            elm.text = shorttitle
            #elm.elementPositionX = LRCornerNumX
            #elm.elementPositionY = LRCornerNumY

        elif elm.name == "smallMapScale":
            elm.text = scale_text

        elif elm.name == "PlotDate":
            now = datetime.datetime.now()
            elm.text = "PLOT DATE: %2d/%02d/%4d" % (now.month, now.day, now.year)
            #elm.elementPositionX = DateX
            #elm.elementPositionY = DateY

        elif elm.name == "Disclaimer" or elm.name == "DisclaimerBox":
#            elm.elementPositionX = DisclaimerX
#            elm.elementPositionY = DisclaimerY
            pass
        #PAGE ELEMENTS
#        elif elm.name == maindf.name:
#            elm.elementPositionX = dataframe_minx
#            elm.elementPositionY = dataframe_miny
#            elm.elementHeight    = dataframe_maxy - dataframe_miny
#            elm.elementWidth     = dataframe_maxx - dataframe_minx

#        elif elm.name == "NorthArrow":
#            elm.elementPositionX = NorthX
#            elm.elementPositionY = NorthY
 
#        elif elm.name == "ScaleBar":
#            elm.elementPositionX = ScaleBarX
#            elm.elementPositionY = ScaleBarY
    return

def update_cancelled_taxlot_table(mxd, mapnumber_arg):

    # Might want to move the "cancelled" table off the page if it's empty???

    # Note that this function is not affected by any query definition.
    table = read_cancelled(ORMapLayers.CANCELLEDNUMBERS_TABLE, mapnumber_arg)
    if not len(table): 
        aprint("Unable to load cancelled numbers from \"%s\" for %s." % (ORMapLayers.CANCELLEDNUMBERS_TABLE, mapnumber_arg))
        return
    aprint("Loaded %d cancelled taxlots." % len(table))

    cancelled_elem = [None, None, None, None]
    ncols = 4 # "can1...can4"
    for x in xrange(0, ncols):
        try:
            cancelled_elem[x] = MAP.ListLayoutElements(mxd, "TEXT_ELEMENT", "can%d" % (x+1))[0]
            cancelled_elem[x].text = " " # Important that this element has some text in it (event just a single space) so ArcMap does not "lose" it.
        except Exception as e:
            aprint("Exception \"e\" when initializing cancelled column %d" % (e,x))
            pass

    max_y, columns = make_table(table, ncols)

    # Adjust the font size of the table according to the number of rows
    fontsize = 10
    maxrows = 10 # ORMapPageLayout.MaxCancelledRows
    if max_y > maxrows: fontsize = 8

    x = 0
    for column in columns:
        cancelled_elem[x].text = column
        cancelled_elem[x].fontSize = fontsize
        x += 1
        
    return

# ==============================================================================
#
# This is the main entry point from the Python Toolbox
#
   
def update_page_layout(mxdname, mapnumber):
    """Update the current map document (CURRENT) page layout using the given map_number."""
    
    mxd = MAP.MapDocument(mxdname)
    print("MXD file = ", mxd.filePath)

    try:
        maindf_name = ORMapLayers.MainDF
    except AttributeError:
        maindf_name = "MainDF"

    mxd = MAP.MapDocument(mxdname)

    maindf = get_dataframe(mxd, maindf_name) 
    mapnumber_query = get_mapnumber_query(mapnumber)

    index_layer = get_layer(mxd, maindf, ORMapLayers.MAPINDEX_LAYER)
    if not index_layer: 
        # can't function without an index layer!
        return
    row = None
    with arcpy.da.SearchCursor(index_layer.dataSource, mapindex_fields, mapnumber_query) as cursor:
        mapindex_scale = 0
        mapindex_mapnumber = ""
        for row in cursor:
            mapindex_mapscale = max(mapindex_scale, row[MAPSCALE])
            if row[MAPNUMBER] and not mapindex_mapnumber or (len(mapindex_mapnumber) > len(row[MAPNUMBER])): 
                mapindex_mapnumber = row[MAPNUMBER]
                mapindex_ormapnum  = row[ORMAPNUM]
                mapindex_cityname  = row[CITYNAME]
    orm = ormapnum()
    orm.unpack(mapindex_ormapnum)

    set_main_definition_queries(mxd, maindf, mapnumber, mapindex_mapscale, mapnumber_query)

    # After setting the defintion query on the index layer, we can just zoom to
    # the extent of that layer to set up the view. After doing that though
    # we still have to set the scale to something useful.   
    maindf.extent = index_layer.getExtent()
    maindf.scale  = mapindex_mapscale
    aprint("Scale: %s" % mapindex_mapscale)

    table_defquery = readtable(mxd, maindf, ORMapLayers.CUSTOMDEFINITIONQUERIES_TABLE, "*", mapnumber_query)
    if not len(table_defquery): aprint("Unable to load optional DefCustomTable \"%s\". Query: %s" % (ORMapLayers.CUSTOMDEFINITIONQUERIES_TABLE, mapnumber_query))

    update_page_elements(mxd, maindf, orm, mapnumber_query, mapindex_mapnumber, mapindex_mapscale, mapindex_cityname)
    update_cancelled_taxlot_table(mxd, mapnumber)
    adjust_masking(mxd, maindf, orm, mapnumber)

    arcpy.RefreshActiveView()

    aprint("That's all.")
    return

# ======================================================================

if __name__ == '__main__':
    try:
        # Try to run as a python script (from a toolbox in arcmap)
        mxdname="CURRENT"
        mapnumber=sys.argv[1]
    except IndexError:
        # Run in the debugger
        mxdname = "TestMap.mxd"
        mapnumber = "8.10.25*"

    aprint("mxdname: %s mapnumber: %s" % (mxdname, mapnumber))
    update_page_layout(mxdname, mapnumber)
    
# That's all
