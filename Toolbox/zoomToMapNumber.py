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
                           GetDataframe, GetLayer, set_definition_query
from ormapnum import ormapnum
from cancellations import read_cancelled, make_table

mapindex_fields = [ "MapScale", "MapNumber", "CityName", "OrMapNum", "SHAPE@", ]
MAPSCALE  = 0
MAPNUMBER = 1
CITYNAME  = 2
ORMAPNUM  = 3
SHAPE     = 4

cancelledfields  = [ "Taxlot", ]
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
    """ Convert a short mapnumber (possibly with a wildcard in it) into a SQL query. """
    
    # I have to use different delimiters for different databases. Sigh.
    mapnumber_field = ORMapLayers.MapNumberField
    delimiter_l = '['
    delimiter_r = ']'
    #wildcard    = '*'
    return "%s%s%s LIKE '%s'" % (delimiter_l, mapnumber_field, delimiter_r, mapnumber)

def set_main_definition_queries(mxd, df, orm, mapnumber, mapscale, query):
    """ Set definition queries for each layer in the main dataframe. 
        SEARCH FOR AN ITEM IN THE DEF QUERY TABLE FIRST... 
        OTHERWISE SET TO CONFIG TABLE VALUES. """

# NOTE "mapnumber" and "mapscale" can be used in config file
# so don't go removing them...
        
# So far, mapscale is not used in any queries... 
        
    arcpy.SetProgressorLabel("Set Main DF definition queries.")
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
#            try:
#                s = d_anno[lyr.name]
#                lyr.visible = (mapscale == s)
#                aprint("%s %s %s" % (lyr.name, mapscale, s))
#            except KeyError:
#                pass

        return

def list_scalebars(mxd):
    sb = []
    # make a list of all the scalebar elements in the map.
    for elem in MAP.ListLayoutElements(mxd, "MAPSURROUND_ELEMENT"):
        if elem.name.find("Scalebar")>=0:
            sb.append(elem)
    return sb

def is_visible(elem, mxd):
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
    sbname = ORMapPageLayout.Scalebars[mapscale] # the one we want
    visible_sb = selected_sb = None
    for elem in sb:
        # Is this scalebar visible?
        if is_visible(elem, mxd):
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

def update_locator_maps(mxd, orm, mapnumber):
    """ Update the locator maps to emphasize the area of interest.
    You can either create a mask or a highlighter based on queries in the configuration.
    Set up query definitions in each dataframe to control this. """

    arcpy.SetProgressorLabel("Update locator maps")

    # TODO - If one of these maps is going to be blank we should probably move it off the map
    
    for dfname,layers,extlayername,scale in [
            (ORMapLayers.LocatorDF,  ORMapLayers.LocatorLayers,  ORMapLayers.LocatorExtentLayer,  ORMapLayers.LocatorScale),
            (ORMapLayers.SectionDF,  ORMapLayers.SectionLayers,  ORMapLayers.SectionExtentLayer,  ORMapLayers.SectionScale),
            (ORMapLayers.QSectionDF, ORMapLayers.QSectionLayers, ORMapLayers.QSectionExtentLayer, ORMapLayers.QSectionScale),
            ]:
        df = GetDataframe(mxd, dfname)
        for layername, qd in layers:
            query = ""
            if qd: 
                query = eval(qd) 
            set_definition_query(mxd, df, layername, query) 
        if extlayername:
            # Pan and zoom are optional in locator maps.
            ext_layer = GetLayer(mxd, df, extlayername)
            df.extent = ext_layer.getExtent()
            if scale: df.scale  = scale

    return

def build_titles(orm, s_cityname):
    """ Build text strings usable for short and long titles and scale text.
    Return them as a tuple. """
    
    shortmaptitle = '%s.%s' % (orm.township, orm.range)
    if orm.section>0: shortmaptitle += ".%d" % orm.section
    if orm.quarter != '0':
        shortmaptitle += orm.quarter
        if orm.quarterquarter != '0': shortmaptitle += orm.quarterquarter
    if s_cityname.strip():
        shortmaptitle += "\n" + s_cityname.replace(",","\n")

    townrng = "T" + str(orm.township) + orm.township_frac + orm.township_dir + ' ' + \
         "R" + str(orm.range)    + orm.range_frac    + orm.range_dir    + " WM"

    longmaptitle = townrng
    if str(orm.section):
        qqtext = orm.qqtext()
        if qqtext:
            l1 = qqtext + " SEC." + str(orm.section)
        else:
            l1 = "SECTION " + str(orm.section)   

        longmaptitle = l1 + ' ' + townrng
        try:
            # If there is a "map suffix" then split the title on 2 lines.
            s_sfx = {'D':'DETAIL', 'S':'SUPPLEMENTAL', 'T':'DETAIL'}[orm.mapsuffixtype]
            longmaptitle = l1 + '\n' + townrng + " %s %d" % (s_sfx, orm.mapsuffixnumber)
        except KeyError:
            pass

    print("\"%s\" \"%s\"" % (shortmaptitle, longmaptitle))
    return shortmaptitle, longmaptitle

def update_page_elements(mxd, df, orm, mapnumber_query, s_mapnum, s_mapscale, s_cityname):
    
    # Allowing changes to the page elements based on settings here
    # would allow a custom set up for each map page, by loading settings
    # from a table.

    arcpy.SetProgressorLabel("Set up page layout elements")
    
    select_scalebar(mxd, s_mapscale)

    # Using a table has the advantage of allowing a custom set up for each page.
    table = readtable(mxd, df, ORMapLayers.PAGELAYOUT_TABLE, pagelayoutfields, mapnumber_query)
    if not len(table):
        # Use configuration - one set up for every map page.
        aprint("Using configuration file for page layout; no PageLayoutTable found. \"%s\". Query: %s" % (ORMapLayers.PAGELAYOUT_TABLE, mapnumber_query))

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

    (shorttitle, longtitle) = build_titles(orm, s_cityname)
    
    # Legacy: I don't use this, I let ArcMap set up scale text.
    scale_text   = "1\" = %d'" % (int(s_mapscale) / 12)

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
    
        elif elm.name == ORMapPageLayout.CancelledTaxlotsElement:
            cancelledtaxlot_count = populate_cancelled_taxlot_table(mxd, s_mapnum)
            offset = 0
            if cancelledtaxlot_count == 0:
                # Move the cancelled taxlot table off the layout
                offset = 4
            elm.elementPositionX = ORMapPageLayout.CancelledTaxlotsXY[0] + offset
            elm.elementPositionY = ORMapPageLayout.CancelledTaxlotsXY[1]
            
            
            
        # Move the locator maps off the page if they are not useful.
           
        elif elm.name == ORMapLayers.SectionDF:
            offset = 4
            if orm.section > 0:
                offset = 0
            elm.elementPositionX = ORMapPageLayout.LocatorSectionXY[0] + offset
            elm.elementPositionY = ORMapPageLayout.LocatorSectionXY[1]


        elif elm.name == ORMapLayers.QSectionDF:
            offset = 4
            if s_mapscale < 24000:
#            if orm.quarter != "0":
                offset = 0
            elm.elementPositionX = ORMapPageLayout.LocatorQSectionXY[0] + offset
            elm.elementPositionY = ORMapPageLayout.LocatorQSectionXY[1]
        
    return

def populate_cancelled_taxlot_table(mxd, mapnumber):
    """ Fill in the cancelled taxlot table in the page. 
        Return the number of cancelled taxlots. """
        
    # Might want to move the "cancelled" table off the page if it's empty???

    arcpy.SetProgressorLabel("Populate cancelled taxlot table")
        
    # Note that this function is not affected by any query definition.
    cancelled_taxlots = read_cancelled(ORMapLayers.CancelledNumbersTable, mapnumber)
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
        maxrows = 10 # ORMapPageLayout.MaxCancelledRows
        if max_y > maxrows: fontsize = 8

        x = 0
        for column in columns:
            cancelled_elem[x].text = column
            cancelled_elem[x].fontSize = fontsize
            x += 1
        
    return len(cancelled_taxlots)

# ==============================================================================

def update_page_layout(mxd, mapnumber):
    """Update the map document page layout using the given map_number."""
    
    orm = ormapnum()
    orm.expand(mapnumber)   # convert short map number to ormap taxlot number

    try:
        maindf_name = ORMapLayers.MainDF
    except AttributeError:
        maindf_name = "MainDF"

    maindf = GetDataframe(mxd, maindf_name)

    mapindex_layer = GetLayer(mxd, maindf, ORMapLayers.MapIndexLayer[0])
    if not mapindex_layer: 
        # can't function without an index layer!
        return
    mapindex_query = eval(ORMapLayers.MapIndexLayer[1])
    row = None
    count = 0
    mapindex_scale = 0
    mapindex_mapnumber = ""
    with arcpy.da.SearchCursor(mapindex_layer.dataSource, mapindex_fields, mapindex_query) as cursor:
        for row in cursor:
            mapindex_mapnumber = row[MAPNUMBER]
            mapindex_ormapnum  = row[ORMAPNUM]
            mapindex_cityname  = row[CITYNAME]
            mapindex_scale     = row[MAPSCALE]
            count += 1
            
    if count != 1:
        eprint("Query \%s\" matched %d records. FIX THIS." % (mapindex_query, count))
        if count == 0: return

    aprint("Read from index file: %s %s %s %s" % (mapindex_mapnumber, mapindex_ormapnum, mapindex_cityname, mapindex_scale))
    mapnumber_query = get_mapnumber_query(mapindex_mapnumber)
    set_main_definition_queries(mxd, maindf, orm, mapindex_mapnumber, mapindex_scale, mapnumber_query)

    # Set definition query, then zoom to extent of layer.
    # then force the scale to the scale defined in the index.
 
    maindf.extent = mapindex_layer.getExtent()
    
    # MapIndex has to have the relative scale not the "1 inch = N feet" scale
    # I can fix there here, it might be better??
    
    lookup_scale = {   10 :   120,
                       20 :   240,
                       30 :   300,
                       40 :   480,
                       50 :   600,
                       60 :   720, 
                      100 :  1200, 
                      200 :  2400, 
                      400 :  4800, 
                     2000 : 24000,
                   }
    try:
        scale = lookup_scale[mapindex_scale]
    except KeyError:
        scale = mapindex_scale # assume it is already recalculated
    maindf.scale  = scale
    aprint("Set main df scale to %d." % scale)
    
#    table_defquery = readtable(mxd, maindf, ORMapLayers.CUSTOMDEFINITIONQUERIES_TABLE, "*", mapnumber_query)
#    if not len(table_defquery): aprint("Unable to load optional DefCustomTable \"%s\". Query: %s" % (ORMapLayers.CUSTOMDEFINITIONQUERIES_TABLE, mapnumber_query))

    update_page_elements(mxd, maindf, orm, mapindex_query, mapindex_mapnumber, scale, mapindex_cityname)
    update_locator_maps(mxd, orm, mapindex_mapnumber)

    arcpy.RefreshActiveView()

    return

def test_layouts():
    for mapnumber in ["8.10", "8.10.5.CD", "8.10.5CD D1", "8.10.5CD D2", ]:
        #mapnumber = "0408.00N10.00W05CD--0000"
        #mapnumber = "0408.00N10.00W05CD--D001"
        #mapnumber = "0408.00N10.00W05CD--D002"

        print("mxdname: %s mapnumber: %s" % (mxdname, mapnumber))
        mxd = MAP.MapDocument(mxdname)
        update_page_layout(mxd, mapnumber)
        del mxd    

# ======================================================================

if __name__ == '__main__':
    try:
        # Try to run as a python script (from a toolbox in arcmap)
        mxdname="CURRENT"
        mapnumber=sys.argv[1]
    except IndexError:
        # Run in the debugger
        mxdname = "TestMap.mxd"
    
    #mxd = MAP.MapDocument(mxdname)
    #select_scalebar(mxd, 24000)
    #del mxd
    test_layouts()

# That's all
