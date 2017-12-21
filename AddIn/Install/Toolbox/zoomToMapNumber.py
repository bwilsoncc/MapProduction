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

featureclassfields = [ "MapScale", "MapNumber", "CityName", "OrMapNum", "SHAPE@", ]
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

def readfeaturelayer(mxd, df, tablename, whereclause):
    """ Read the first row from a feature layer.
    This presumes that there is a definition query set on the layer,
    so there should only be a few rows visible. """
    
    layer = row = None
    try:
        layer = MAP.ListLayers(mxd, tablename, df)[0]
        layer.definitionQuery = "" # clear out the old definition query
    except IndexError:
        eprint("Not found: table=\"%s\" query=\"%s\"" % (tablename, whereclause))
        return None
    with arcpy.da.SearchCursor(layer, featureclassfields, whereclause) as cursor:
        try:    
            row = cursor.next()
        except Exception as e:
            aprint("No data-- \"%s\" %s \"%s\" : \"%s\"" % (layer, featureclassfields, whereclause, e))

    return row

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

def set_definition_queries(mxd, df, query):
#SET QUERY DEFINITIONS FOR EACH LAYER.  SEARCH FOR AN ITEM IN THE DEF QUERY TABLE FIRST... OTHERWISE SET TO CONFIG TABLE VALUES.
    table_defquery = readtable(mxd, df, ORMapLayers.CUSTOMDEFINITIONQUERIES_TABLE, "*", query)
    if len(table_defquery):
        #-- Items stored in long string input defQueryString field.  Pull them out and into their own array.
        defQueryList = table_defquery.defQueryString.split(";")
        defQueryLayers = []
        defQueryValues = []
        for defQueryItem in defQueryList:
            lyr,qry = defQueryItem.split(":")
            defQueryLayers.append(lyr)
            defQueryValues.append(qry)
        for lyr in MAP.ListLayers(mxd, "", df):
            if lyr.supports("DATASETNAME"):
                if lyr.name in defQueryLayers:
                    lyr.definitionQuery = defQueryValues[defQueryLayers.index(lyr.name)]

    else:
        aprint("Unable to load optional DefCustomTable \"%s\". Query: %s" % (ORMapLayers.CUSTOMDEFINITIONQUERIES_TABLE, query))
        # Define all the layername, query definition pairs as a list of tuples.
        # Add on the "EXTRA" layers (20 of them)
        # Then evaluate (using "eval()" each expression so that the script does not choke
        # if a layer is not defined in the config file.
    
        l_layers = [
                ("ORMapLayers.LOTSANNO_LAYER", "ORMapLayers.LOTSANNO_QD"),
                ("ORMapLayers.PLATSANNO_LAYER", "ORMapLayers.PLATSANNO_QD"),
                ("ORMapLayers.TAXCODEANNO_LAYER", "ORMapLayers.TAXCODEANNO_QD"),
                ("ORMapLayers.TAXNUMANNO_LAYER", "ORMapLayers.TAXNUMANNO_QD"),
                ("ORMapLayers.ACRESANNO_LAYER", "ORMapLayers.ACRESANNO_QD"),
                ("ORMapLayers.ANNO10_LAYER", "ORMapLayers.ANNO10_QD"),
                ("ORMapLayers.ANNO20_LAYER", "ORMapLayers.ANNO20_QD"),
                ("ORMapLayers.ANNO30_LAYER", "ORMapLayers.ANNO30_QD"),
                ("ORMapLayers.ANNO40_LAYER", "ORMapLayers.ANNO40_QD"),
                ("ORMapLayers.ANNO50_LAYER", "ORMapLayers.ANNO50_QD"),
                ("ORMapLayers.ANNO60_LAYER", "ORMapLayers.ANNO60_QD"),
                ("ORMapLayers.ANNO100_LAYER", "ORMapLayers.ANNO100_QD"),
                ("ORMapLayers.ANNO200_LAYER", "ORMapLayers.ANNO200_QD"),
                ("ORMapLayers.ANNO400_LAYER", "ORMapLayers.ANNO400_QD"),
                ("ORMapLayers.ANNO800_LAYER", "ORMapLayers.ANNO800_QD"),
                ("ORMapLayers.ANNO2000_LAYER", "ORMapLayers.ANNO2000_QD"),
                ("ORMapLayers.CORNER_ABOVE_LAYER", "ORMapLayers.CORNER_ABOVE_QD"),
                ("ORMapLayers.TAXCODELINES_ABOVE_LAYER", "ORMapLayers.TAXCODELINES_ABOVE_QD"),
                ("ORMapLayers.TAXLOTLINES_ABOVE_LAYER", "ORMapLayers.TAXLOTLINES_ABOVE_QD"),
                ("ORMapLayers.REFLINES_ABOVE_LAYER", "ORMapLayers.REFLINES_ABOVE_QD"),
                ("ORMapLayers.CARTOLINES_ABOVE_LAYER", "ORMapLayers.CARTOLINES_ABOVE_QD"),
                ("ORMapLayers.WATERLINES_ABOVE_LAYER", "ORMapLayers.WATERLINES_ABOVE_QD"),
                ("ORMapLayers.WATER_ABOVE_LAYER", "ORMapLayers.WATER_ABOVE_QD"),
                ("ORMapLayers.MAPINDEXSEEMAP_LAYER", "ORMapLayers.MAPINDEXSEEMAP_QD"),
                ("ORMapLayers.MAPINDEX_LAYER", "ORMapLayers.MAPINDEX_QD"),
                ("ORMapLayers.CORNER_BELOW_LAYER", "ORMapLayers.CORNER_BELOW_QD"),
                ("ORMapLayers.TAXCODELINES_BELOW_LAYER", "ORMapLayers.TAXCODELINES_BELOW_QD"),
                ("ORMapLayers.TAXLOTLINES_BELOW_LAYER", "ORMapLayers.TAXLOTLINES_BELOW_QD"),
                ("ORMapLayers.REFLINES_BELOW_LAYER", "ORMapLayers.REFLINES_BELOW_QD"),
                ("ORMapLayers.CARTOLINES_BELOW_LAYER", "ORMapLayers.CARTOLINES_BELOW_QD"),
                ("ORMapLayers.WATERLINES_BELOW_LAYER", "ORMapLayers.WATERLINES_BELOW_QD"),
                ("ORMapLayers.WATER_BELOW_LAYER", "ORMapLayers.WATER_BELOW_QD"),
                ]
        for extra in range(1,20):
            l_layers.append(
                    ("ORMapLayers.EXTRA%d_LAYER" % extra,
                     "ORMapLayers.EXTRA%d_QD" % extra)
                    )

        # Now we have all the layers and queries in one place, l_list.
        # Convert them into a dictionary
        d_layers = {}
        for (v_lyrname,v_dq) in l_layers:
            try:
                layername = eval(v_lyrname)
                dq    = eval(v_dq)
                d_layers[layername] = dq                    
            except AttributeError as e:
                print("Configuration not found; ignoring it. %s" % e)

        # Now make one pass through the dataframe and fix up the definition queries.

        for lyr in MAP.ListLayers(mxd, "", df):
            if lyr.supports("DATASETNAME"):
                try:
                    dq = d_layers[lyr.name]
                    query = ""
                    if dq:
                        eprint("ARGHHH FIX THIS")
#                        query = dq.replace("*MapNumber*", s_mapnum).replace("*MapScale*", s_mapscale)
                    aprint("layername: %s query: \"%s\"" % (lyr.name, query))
                    lyr.definitionQuery = query

                except KeyError:
                    print("No need to touch layer \"%s\"." % lyr.name)
        return

def update_pagelayout(mxd, df, mapnumber):  

    table = readtable(mxd, df, ORMapLayers.PAGELAYOUT_TABLE, pagelayoutfields, mapnumber_query)
    if not len(table): aprint("Unable to load PageLayoutTable \"%s\". Query: %s" % (ORMapLayers.PAGELAYOUT_TABLE, mapnumber_query))

    aprint("Processing MapNumber '%s'." % mapnumber)
    if not table:
        aprint("Using configuration file for page layout.")

#        DataFrameMinX = ORMapPageLayout.DataFrameMinX
#        DataFrameMinY = ORMapPageLayout.DataFrameMinY
#        DataFrameMaxX = ORMapPageLayout.DataFrameMaxX
#        DataFrameMaxY = ORMapPageLayout.DataFrameMaxY
#        df.extent = extent
#       df.rotation = ORMapPageLayout.MapAngle
        
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
        #SET PAGE LAYOUT LOCATIONS FROM PAGELAYOUT TABLE
        aprint("Loading Page Layout items from PAGELAYOUTTABLE")
        
            # fix please

#        DataFrameMinX = pagelayoutrow.DataFrameMinX
#        DataFrameMinY = pagelayoutrow.DataFrameMinY
#        DataFrameMaxX = pagelayoutrow.DataFrameMaxX
#        DataFrameMaxY = pagelayoutrow.DataFrameMaxY

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
    return

def adjust_masking(mxd, maindf, orm, mapnumber):
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

    #--- Set up the definition query on each data framelayer to highlight polygons.
    query = ""
    try:
        if mapnumber: query = ORMapLayers.MAPINDEXMASK_QD % mapnumber 
    except Exception as e:
        aprint("Query setup failed: '%s' '%s' %s" % (ORMapLayers.MAPINDEXMASK_QD, mapnumber, e))
    set_definition_query(mxd, maindf, ORMapLayers.MAPINDEXMASK_LAYER, query)

    query = ""
    if mapnumber: query = ORMapLayers.LOCATOR_QD % (int(orm.township), int(orm.range), orm.range_dir) 
    set_definition_query(mxd, locatordf, ORMapLayers.LOCATOR_LAYER, query)

    query = ""
    if orm.section: query = ORMapLayers.SECTIONS_QD % orm.section
    set_definition_query(mxd, sectionsdf, ORMapLayers.SECTIONS_LAYER, query)
        
    query = ORMapLayers.QSECTIONS_QD % qqwhere(orm.quarter, orm.quarterquarter)
    set_definition_query(mxd, qsectionsdf, ORMapLayers.QTRSECTIONS_LAYER, query)

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

def update_page_elements(mxd, orm, s_mapnum, s_mapscale, s_cityname):
    
    # Philosophical note:
    # A lot of this code is commented out because I think
    # the map document settings should be retained,
    # if you want the map arrow to appear in a certain spot
    # for example, adjust the map document not the config settings.
    
    (shorttitle, longtitle, scale_text) = build_titles(orm, s_mapscale, s_cityname)
    
    #REPOSITION AND MODIFY PAGE ELEMENTS
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
#            elm.elementHeight = DataFrameMaxY - DataFrameMinY
#            elm.elementPositionX = DataFrameMinX
#            elm.elementPositionY = DataFrameMinY
#            elm.elementWidth = DataFrameMaxX - DataFrameMinX

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

    # I have to use different delimiters for different databases. Sigh.
    mapnumber_field = ORMapLayers.MapNumberField
    delimiter_l = '['
    delimiter_r = ']'
    #wildcard    = '*'
    mapnumber_query = "%s%s%s LIKE '%s'" % (delimiter_l, mapnumber_field, delimiter_r, mapnumber)

    # NOTE NOTE you have to set the definition queries BEFORE reading data.
    
    mapindexrow = readfeaturelayer(mxd, maindf, ORMapLayers.MAPINDEX_LAYER, mapnumber_query)
    if not mapindexrow: eprint("Unable to read MapNumber in feature class \"%s\". Query: %s" % (ORMapLayers.MAPINDEX_LAYER, mapnumber_query))

    #COLLECT MAP INDEX POLYGON INFORMATION AND GET FEATURE EXTENT
    geom = mapindexrow[SHAPE]
    # Can I get the layer extent here instead of the feature
    # since I just selected N features not just one?

    #GET OTHER TABLE ATTRIBUTES
    s_mapscale = str(mapindexrow[MAPSCALE])
    this_mapnumber = mapindexrow[MAPNUMBER]
    s_ormapnum = mapindexrow[ORMAPNUM]
    s_cityname = mapindexrow[CITYNAME]

    #MODIFY MAIN DATAFRAME PROPERTIES
    maindf.extent   = geom.extent
    maindf.scale    = s_mapscale

    orm = ormapnum()
    orm.unpack(s_ormapnum)

    table_defquery = readtable(mxd, maindf, ORMapLayers.CUSTOMDEFINITIONQUERIES_TABLE, "*", mapnumber_query)
    if not len(table_defquery): aprint("Unable to load optional DefCustomTable \"%s\". Query: %s" % (ORMapLayers.CUSTOMDEFINITIONQUERIES_TABLE, mapnumber_query))

    update_page_elements(mxd, orm, this_mapnumber, s_mapscale, s_cityname)
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
        mapnumber = "8.10.8BB"

    aprint("mxdname: %s mapnumber: %s" % (mxdname, mapnumber))
    update_page_layout(mxdname, mapnumber)
    
# That's all
