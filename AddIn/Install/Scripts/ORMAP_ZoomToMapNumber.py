### ---------------------------------------------------------------------------
### Ormap_ZoomToMap.py
### Created by: Shad Campbell
### Date: 3/11/2011
### Updated by:
### Description: This script zooms and configures a map based upon the MapNumber
### and PageSize arguemnents passed into it.  It is used by itself and also used
### when printing/exporting.
### ---------------------------------------------------------------------------
##
from __future__ import print_function
import arcpy, arcpy.mapping as MAP
import pythonaddins
import os, sys
import datetime
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

# NB, force string into lower case to make sure it works in Windows
configpath = os.path.dirname(__file__).lower().replace('scripts', 'config')
sys.path.append(configpath)

def aprint(msg):
    """ Print a message. Execution does not stop. """
    print(msg)
    sys.stdout.flush()
    arcpy.AddMessage(msg)

def eprint(msg):
    """ Print a message. Execution will stop when you use this one. """
    print("ERROR:",msg)
    arcpy.AddError(msg)

# Load the "configuration files"
import ORMAP_LayersConfig as OrmapLayers
import ORMAP_MapConfig as PageConfig

# ==============================================================================

def load_config():
    """ Load the configuration options used in this tool, or load defaults. """
    global maindf_name, locatordf_name, sectionsdf_name, qsectionsdf_name
    try:
        maindf_name = OrmapLayers.MainDF
    except AttributeError:
        maindf_name = "MainDF"
    try:
        locatordf_name = OrmapLayers.LocatorDF
    except AttributeError:
        locatordf_name = "LocatorDF"
    try:
        sectionsdf_name = OrmapLayers.SectionsDF
    except AttributeError:
        sectionsdf_name = "SectionsDF"
    try:
        qsectionsdf_name = OrmapLayers.QSectionsDF
    except AttributeError:
        qsectionsdf_name = "QSectionsDF"
    return

def load_dataframe(mxd, dfname):
    """ Load the dataframe object. """
    df = None
    try:
        df = MAP.ListDataFrames(mxd, dfname)[0]
    except Exception as e:
        eprint("Dataframe not found. Make sure it is named '%s'." % dfname)
        eprint(e)
    return df

def readfeaturelayer(mxd, df, tablename, whereclause):
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

def set_definition(mxd, df, layername, query):
    """ Set the definition query on a layer. """
    if df:
        try:
            layer = MAP.ListLayers(mxd, layername, df)[0]
            layer.definitionQuery = query
            aprint("layer: \"%s\" query: \"%s\"" % (layername, query))
        except Exception as e:
            eprint("Can't set query \"%s\" on layer \"%s\". \"%s\"" % (query, layername, e))
            return False
    return True

def qqwhere(q, qq):
    """ return a query string based on the quarter and quarterquarter letters 0ABCD """
    rval = "" # Nothing is highlighted
    if q != '0':
        if qq == '0':
            # Entire quarter is highlighted
            rval = q
        else:
            # One quarter quarter is highlighted
            rval = q + qq
    return rval

# ==============================================================================

# This is the mapnumber you typed in the ArcGIS dialog, so it can contain
# wildcard charaacters. If it fails to match anything that is your problem. :-)
mapnumber_arg = arcpy.GetParameterAsText(0)
if not mapnumber_arg: mapnumber_arg = "8.10.25%" # debugging...

##PageSize = arcpy.GetParameterAsText(1)

load_config()

# TODO detect if this is a toolbar or we're in a toolbox or standalone
# and set up map document accordingly.

document_name = "CURRENT"
#document_name = os.path.join("C:/GeoModel/Clatsop/MapProduction18x24.mxd")
mxd = MAP.MapDocument(document_name)

#aprint("MXD: %s" % document_name)
#for df in MAP.ListDataFrames(mxd, "*"):
#    aprint("Dataframe: %s" % df.name)

maindf      = load_dataframe(mxd, maindf_name)
locatordf   = load_dataframe(mxd, locatordf_name)
sectionsdf  = load_dataframe(mxd, sectionsdf_name)
qsectionsdf = load_dataframe(mxd, qsectionsdf_name)

delimiter_l = '['
delimiter_r = ']'
wildcard    = '*'
# Just how stupid is it when I have to use different delimiters
# for different databases. Sigh.
mapnumber_query = "%sMapNumber%s LIKE '%s'" % (delimiter_l, delimiter_r, mapnumber_arg)
#query = "[MapNumber] LIKE '8.10.25*'" # uncomment only for DEBUGGING
aprint(mapnumber_query)

mapindexrow = readfeaturelayer(mxd, maindf, OrmapLayers.MAPINDEX_LAYER, mapnumber_query)
if not mapindexrow: eprint("Unable to read MapNumber in feature class \"%s\". Query: %s" % (OrmapLayers.MAPINDEX_LAYER, mapnumber_query))

table_pagelayout = readtable(mxd, maindf, OrmapLayers.PAGELAYOUT_TABLE, pagelayoutfields, mapnumber_query)
if not len(table_pagelayout): aprint("Unable to load PageLayoutTable \"%s\". Query: %s" % (OrmapLayers.PAGELAYOUT_TABLE, mapnumber_query))

table_cancelled = read_cancelled(OrmapLayers.CANCELLEDNUMBERS_TABLE, mapnumber_arg)
if len(table_cancelled): 
    aprint("Loaded %d cancelled taxlots." % len(table_cancelled))
else:
    aprint("Unable to load cancelled numbers from \"%s\" for %s." % (OrmapLayers.CANCELLEDNUMBERS_TABLE, mapnumber_arg))

table_defquery = readtable(mxd, maindf, OrmapLayers.CUSTOMDEFINITIONQUERIES_TABLE, "*", mapnumber_query)
if not len(table_defquery): aprint("Unable to load optional DefCustomTable \"%s\". Query: %s" % (OrmapLayers.CUSTOMDEFINITIONQUERIES_TABLE, mapnumber_query))

aprint("Processing MapNumber '%s'." % mapnumber_arg)

geom = mapindexrow[SHAPE]
extent = geom.extent
# Can I get the layer extent here instead of the feature
# since I just selected N features not just one?

#COLLECT MAP INDEX POLYGON INFORMATION AND GET FEATURE EXTENT

if not len(table_pagelayout):
    #SET PAGE LAYOUT LOCATIONS FROM CONFIG
    aprint("Reading Page Layout items from Configuration File")
    DataFrameMinX = PageConfig.DataFrameMinX
    DataFrameMinY = PageConfig.DataFrameMinY
    DataFrameMaxX = PageConfig.DataFrameMaxX
    DataFrameMaxY = PageConfig.DataFrameMaxY
    mapExtent = extent
    map_angle = PageConfig.MapAngle
    TitleX = PageConfig.TitleX
    TitleY = PageConfig.TitleY
    DisclaimerX = PageConfig.DisclaimerX
    DisclaimerY = PageConfig.DisclaimerY
    CancelNumX = PageConfig.CancelNumX
    CancelNumY = PageConfig.CancelNumY
    DateX = PageConfig.DateX
    DateY = PageConfig.DateY
    URCornerNumX = PageConfig.URCornerNumX
    URCornerNumY = PageConfig.URCornerNumY
    LRCornerNumX = PageConfig.LRCornerNumX
    LRCornerNumY = PageConfig.LRCornerNumY
    ScaleBarX = PageConfig.ScaleBarX
    ScaleBarY = PageConfig.ScaleBarY
    NorthX = PageConfig.NorthX
    NorthY = PageConfig.NorthY

else:
    #SET PAGE LAYOUT LOCATIONS FROM PAGELAYOUT TABLE
    aprint("Loading Page Layout items from PAGELAYOUTTABLE")
    map_angle = table_pagelayout[0][ANGLE]
    
    #and so on... fix please

    DataFrameMinX = pagelayoutrow.DataFrameMinX
    DataFrameMinY = pagelayoutrow.DataFrameMinY
    DataFrameMaxX = pagelayoutrow.DataFrameMaxX
    DataFrameMaxY = pagelayoutrow.DataFrameMaxY

    MapPositionX = pagelayoutrow.MapPositionX
    MapPositionY = pagelayoutrow.MapPositionY

    mapExtent = arcpy.Extent(MapPositionX-1, MapPositionY-1, MapPositionX+1, MapPositionY+1)

    MapAngle = pagelayoutrow.MapAngle
    TitleX = pagelayoutrow.TitleX
    TitleY = pagelayoutrow.TitleY
    DisclaimerX = pagelayoutrow.DisclaimerX
    DisclaimerY = pagelayoutrow.DisclaimerY
    CancelNumX = pagelayoutrow.CancelNumX
    CancelNumY = pagelayoutrow.CancelNumY
    DateX = pagelayoutrow.DateX
    DateY = pagelayoutrow.DateY
    URCornerNumX = pagelayoutrow.URCornerNumX
    URCornerNumY = pagelayoutrow.URCornerNumY
    LRCornerNumX = pagelayoutrow.LRCornerNumX
    LRCornerNumY = pagelayoutrow.LRCornerNumY
    ScaleBarX = pagelayoutrow.ScaleBarX
    ScaleBarY = pagelayoutrow.ScaleBarY
    NorthX = pagelayoutrow.NorthX
    NorthY = pagelayoutrow.NorthY

#MISC Relative Map Distances
CountyNameDist = PageConfig.CountyNameDist
MapScaleDist = PageConfig.MapScaleDist

#GET OTHER TABLE ATTRIBUTES
s_mapscale = str(mapindexrow[MAPSCALE])
s_mapnum   = mapindexrow[MAPNUMBER]
s_ormapnum = mapindexrow[ORMAPNUM]
s_cityname = mapindexrow[CITYNAME]

#SET QUERY DEFINITIONS FOR EACH LAYER.  SEARCH FOR AN ITEM IN THE DEF QUERY TABLE FIRST... OTHERWISE SET TO CONFIG TABLE VALUES.
if len(table_defquery):

    #-- Items stored in long string input defQueryString field.  Pull them out and into their own array.
    defQueryList = table_defquery.defQueryString.split(";")
    defQueryLayers = []

    for defQueryItem in defQueryList:
        lyr,qry = defQueryItem.split(":")
        defQueryLayers.append(lyr)
        defQueryValues.append(qry)

    for lyr in MAP.ListLayers(mxd, "", maindf):
        if lyr.supports("DATASETNAME"):
            if lyr.name in defQueryLayers:
                lyr.definitionQuery = defQueryValues[defQueryLayers.index(lyr.name)]

else:
    # Define all the layername, query definition pairs as a list of tuples.
    # Add on the "EXTRA" layers (20 of them)
    # Then evaluate (using "eval()" each expression so that the script does not choke
    # if a layer is not defined in the config file.
    
    l_layers = [
        ("OrmapLayers.LOTSANNO_LAYER", "OrmapLayers.LOTSANNO_QD"),
        ("OrmapLayers.PLATSANNO_LAYER", "OrmapLayers.PLATSANNO_QD"),
        ("OrmapLayers.TAXCODEANNO_LAYER", "OrmapLayers.TAXCODEANNO_QD"),
        ("OrmapLayers.TAXNUMANNO_LAYER", "OrmapLayers.TAXNUMANNO_QD"),
        ("OrmapLayers.ACRESANNO_LAYER", "OrmapLayers.ACRESANNO_QD"),
        ("OrmapLayers.ANNO10_LAYER", "OrmapLayers.ANNO10_QD"),
        ("OrmapLayers.ANNO20_LAYER", "OrmapLayers.ANNO20_QD"),
        ("OrmapLayers.ANNO30_LAYER", "OrmapLayers.ANNO30_QD"),
        ("OrmapLayers.ANNO40_LAYER", "OrmapLayers.ANNO40_QD"),
        ("OrmapLayers.ANNO50_LAYER", "OrmapLayers.ANNO50_QD"),
        ("OrmapLayers.ANNO60_LAYER", "OrmapLayers.ANNO60_QD"),
        ("OrmapLayers.ANNO100_LAYER", "OrmapLayers.ANNO100_QD"),
        ("OrmapLayers.ANNO200_LAYER", "OrmapLayers.ANNO200_QD"),
        ("OrmapLayers.ANNO400_LAYER", "OrmapLayers.ANNO400_QD"),
        ("OrmapLayers.ANNO800_LAYER", "OrmapLayers.ANNO800_QD"),
        ("OrmapLayers.ANNO2000_LAYER", "OrmapLayers.ANNO2000_QD"),
        ("OrmapLayers.CORNER_ABOVE_LAYER", "OrmapLayers.CORNER_ABOVE_QD"),
        ("OrmapLayers.TAXCODELINES_ABOVE_LAYER", "OrmapLayers.TAXCODELINES_ABOVE_QD"),
        ("OrmapLayers.TAXLOTLINES_ABOVE_LAYER", "OrmapLayers.TAXLOTLINES_ABOVE_QD"),
        ("OrmapLayers.REFLINES_ABOVE_LAYER", "OrmapLayers.REFLINES_ABOVE_QD"),
        ("OrmapLayers.CARTOLINES_ABOVE_LAYER", "OrmapLayers.CARTOLINES_ABOVE_QD"),
        ("OrmapLayers.WATERLINES_ABOVE_LAYER", "OrmapLayers.WATERLINES_ABOVE_QD"),
        ("OrmapLayers.WATER_ABOVE_LAYER", "OrmapLayers.WATER_ABOVE_QD"),
        ("OrmapLayers.MAPINDEXSEEMAP_LAYER", "OrmapLayers.MAPINDEXSEEMAP_QD"),
        ("OrmapLayers.MAPINDEX_LAYER", "OrmapLayers.MAPINDEX_QD"),
        ("OrmapLayers.CORNER_BELOW_LAYER", "OrmapLayers.CORNER_BELOW_QD"),
        ("OrmapLayers.TAXCODELINES_BELOW_LAYER", "OrmapLayers.TAXCODELINES_BELOW_QD"),
        ("OrmapLayers.TAXLOTLINES_BELOW_LAYER", "OrmapLayers.TAXLOTLINES_BELOW_QD"),
        ("OrmapLayers.REFLINES_BELOW_LAYER", "OrmapLayers.REFLINES_BELOW_QD"),
        ("OrmapLayers.CARTOLINES_BELOW_LAYER", "OrmapLayers.CARTOLINES_BELOW_QD"),
        ("OrmapLayers.WATERLINES_BELOW_LAYER", "OrmapLayers.WATERLINES_BELOW_QD"),
        ("OrmapLayers.WATER_BELOW_LAYER", "OrmapLayers.WATER_BELOW_QD"),
    ]
    for extra in range(1,20):
        l_layers.append(
            ("OrmapLayers.EXTRA%d_LAYER" % extra,
             "OrmapLayers.EXTRA%d_QD" % extra)
        )

    # Now we have all the layers and queries in one place, l_list.
    # Convert them into a dictionary
    d_layers = {}
    for (v_lyrname,v_qd) in l_layers:
        try:
            layername = eval(v_lyrname)
            qd    = eval(v_qd)
            d_layers[layername] = qd                    
        except AttributeError as e:
            print("Configuration not found; ignoring it. %s" % e)

    # Now make one pass through the dataframe and fix up the definition queries.

    for lyr in MAP.ListLayers(mxd, "", maindf):
        if lyr.supports("DATASETNAME"):
            try:
                qd = d_layers[lyr.name]
                query = ""
                if qd:
                    query = qd.replace("*MapNumber*", s_mapnum).replace("*MapScale*", s_mapscale)
                aprint("layername: %s query: \"%s\"" % (lyr.name, query))
                lyr.definitionQuery = query

            except KeyError:
                print("No need to touch layer \"%s\"." % lyr.name)

#PARSE ORMAP MAPNUMBER TO DEVELOP MAP TITLE
# example
# u'0408.00N10.00W25AD--0000'

orm = ormapnum()
orm.unpack(s_ormapnum)

shortmaptitle = ('%s.%s.%s' % (orm.township, orm.range, orm.section)).rstrip('.')
if orm.quarter != '0':
    shortmaptitle += orm.quarter
    if orm.quarterquarter != '0':  shortmaptitle += orm.quarterquarter
if s_cityname.strip():
    shortmaptitle += "\n" + s_cityname.replace(",","\n")

#CREATE TEXT FOR LONG MAP TITLE BASED ON SCALE FORMATS PROVIDED BY DOR.

scale_text   = "1\" = %d'" % (int(s_mapscale) / 12)

longmaptitle = ""
l24000 = "T" + str(orm.township) + orm.township_frac + orm.township_dir + ' ' + \
         "R" + str(orm.range)    + orm.range_frac    + orm.range_dir    + " WM"
section_text = orm.qqtext()
if s_mapscale == "24000":
    longmaptitle = l24000
elif s_mapscale == "4800":
    longmaptitle = "SECTION " + str(orm.section) + " " + l24000

#elif s_mapscale == "2400":
#    longmaptitle = str(sSectionText) + " SEC." + str(sSection) + " "
#                 + l24000
#elif s_mapscale == "1200":
#    longmaptitle = str(sSectionText) + " SEC." + str(sSection) + " "
#                 + l24000
else:
    longmaptitle = section_text + " SEC." + str(orm.section) + " " + l24000
                 
    if str(section_text)=="":
        longmaptitle = "SECTION " + str(orm.section) + " " + l24000
    if str(orm.section)=="":
        longmaptitle = l24000

#MODIFY TITLE FOR NON-STANDARD MAPS
if orm.maptype == "S":
    longmaptitle = "SUPPLEMENTAL MAP NO. %d\n" % orm.mapnumber + longmaptitle
elif orm.maptype == "D":
    longmaptitle = "DETAIL MAP NO. %d\n" % orm.mapnumber + longmaptitle
elif orm.maptype == "T":
    longmaptitle = "SHEET NO. %d\n" % orm.mapnumber + longmaptitle


#REPOSITION AND MODIFY PAGE ELEMENTS
for elm in MAP.ListLayoutElements(mxd):
    #TEXT ELEMENTS
    if elm.name=="MapNumber":
        elm.text = s_mapnum
        
    if elm.name.lower() == "mainmaptitle":
        elm.text = longmaptitle
        #elm.elementPositionX = TitleX
        #elm.elementPositionY = TitleY
        
    if elm.name.lower() == "smallmaptitle":
        elm.text = longmaptitle
                
    if elm.name == "CountyName":
        elm.text = PageConfig.CountyName
        elm.elementPositionX = TitleX
        elm.elementPositionY = TitleY - CountyNameDist
        
    if elm.name == "MainMapScale":
        elm.text = scale_text
        elm.elementPositionX = TitleX
        elm.elementPositionY = TitleY - MapScaleDist

    if elm.name == "UpperLeftMapNum":
        elm.text = shortmaptitle
        
    if elm.name == "UpperRightMapNum":
        elm.text = shortmaptitle
        #elm.elementPositionX = URCornerNumX
        #elm.elementPositionY = URCornerNumY
        
    if elm.name == "LowerLeftMapNum":
        elm.text = shortmaptitle
        
    if elm.name == "LowerRightMapNum":
        elm.text = shortmaptitle
        #elm.elementPositionX = LRCornerNumX
        #elm.elementPositionY = LRCornerNumY

    if elm.name == "smallMapScale":
        elm.text = scale_text
        
    if elm.name == "PlotDate":
        now = datetime.datetime.now()
        elm.text = "PLOT DATE: %2d/%02d/%4d" % (now.month, now.day, now.year)
        #elm.elementPositionX = DateX
        #elm.elementPositionY = DateY
    if elm.name == "Disclaimer" or elm.name == "DisclaimerBox":
        elm.elementPositionX = DisclaimerX
        elm.elementPositionY = DisclaimerY

    #PAGE ELEMENTS
    if elm.name == maindf.name:
        elm.elementHeight = DataFrameMaxY - DataFrameMinY
        elm.elementPositionX = DataFrameMinX
        elm.elementPositionY = DataFrameMinY
        elm.elementWidth = DataFrameMaxX - DataFrameMinX

    if elm.name == "NorthArrow":
        elm.elementPositionX = NorthX
        elm.elementPositionY = NorthY
 
    if elm.name == "ScaleBar":
        elm.elementPositionX = ScaleBarX
        elm.elementPositionY = ScaleBarY

    if table_cancelled:
        cancelled_elem = [None, None, None, None]
        ncols = 4 # "can1...can4"
        for x in xrange(0, ncols):
            try:
                cancelled_elem[x] = MAP.ListLayoutElements(mxd, "TEXT_ELEMENT", "can%d" % (x+1))[0]
                cancelled_elem[x].text = " " # Important that this element has some text in it (event just a single space) so ArcMap does not "lose" it.
            except Exception as e:
                aprint("Exception \"e\" when initializing cancelled column %d" % (e,x))
                pass

#        maxRows = PageConfig.MaxCancelledRows
        x = 0
        max_y, columns = make_table(table_cancelled, ncols)
        fontsize = 10
        if max_y>10: fontsize = 8

        for column in columns:
            cancelled_elem[x].text = column
            cancelled_elem[x].fontSize = fontsize
            x += 1

#MODIFY MAIN DATAFRAME PROPERTIES
maindf.extent   = mapExtent
maindf.scale    = s_mapscale
maindf.rotation = map_angle

#--- Set up the definition query on each data framelayer to highlight polygons.

query = ""
try:
    if s_mapnum: query = OrmapLayers.MAPINDEXMASK_QD % mapnumber_arg 
except Exception as e:
    aprint("Query setup failed: '%s' '%s' %s" % (OrmapLayers.MAPINDEXMASK_QD, mapnumber_arg, e))
set_definition(mxd, maindf, OrmapLayers.MAPINDEXMASK_LAYER, query)

query = ""
if s_mapnum: query = OrmapLayers.LOCATOR_QD % (int(orm.township), int(orm.range), orm.range_dir) 
set_definition(mxd, locatordf, OrmapLayers.LOCATOR_LAYER, query)

query = ""
if orm.section: query = OrmapLayers.SECTIONS_QD % orm.section
set_definition(mxd, sectionsdf, OrmapLayers.SECTIONS_LAYER, query)
        
query = OrmapLayers.QSECTIONS_QD % qqwhere(orm.quarter, orm.quarterquarter)
set_definition(mxd, qsectionsdf, OrmapLayers.QTRSECTIONS_LAYER, query)


arcpy.RefreshActiveView()

aprint("That's all.")
