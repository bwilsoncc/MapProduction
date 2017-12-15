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

fields = [ "SHAPE@", "MapScale", "MapNumber", "CityName", "OrMapNum"]
SHAPE     = 0
MAPSCALE  = 1
MAPNUMBER = 2
CITYNAME  = 3
ORMAPNUM  = 4

# NB, force string into lower case to make sure it works in Windows
sys.path.append(os.path.dirname(__file__).lower().replace('scripts', 'config')) #path to config files

# Load the "configuration files"
import ORMAP_LayersConfig as OrmapLayers
import ORMAP_MapConfig as PageConfig

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

def getrow(mxd, df, tablename, whereclause):
    layer = row = None
    try:
        layer = MAP.ListLayers(mxd, tablename, df)[0]
    except IndexError:
        eprint("table=\"%s\" query=\"%s\"" % (tablename, whereclause))
        return None

    cursor = arcpy.da.SearchCursor(layer, fields, whereclause)
    try:    
        row = cursor.next()
    except Exception as e:
        aprint("No data-- %s" % e)
    if not row:
        print("WAAAAA")
    del cursor    
    return row

def getcancelled(mxd, df, tablename, whereclause):
    """ Read a table of values to be displayed as cancelled taxlot numbers. """
    layer = row = None
    rows = []
    try:
        layer = MAP.ListLayers(mxd, tablename, df)[0]
    except IndexError:
        eprint("table=\"%s\" query=\"%s\"" % (tablename, whereclause))
        return rows

    with arcpy.da.SearchCursor(layer, fields, whereclause) as cursor:
        for row in cursor:
            rows.append(row)
    return rows

def aprint(msg):
    print(msg)
    sys.stdout.flush()
    arcpy.AddMessage(msg)

def eprint(msg):
    print("ERROR:",msg)
    sys.stdout.flush()
    arcpy.AddError(msg)

load_config()

mapnumber = arcpy.GetParameterAsText(0)
if not mapnumber: mapnumber = "8.10.25%" # debugging...

##PageSize = arcpy.GetParameterAsText(1)

##import ORMAP_18x20MapConfig
##import ORMAP_18x24MapConfig
##if PageSize=='18x20':
##    PageConfig = ORMAP_18x20MapConfig
##else:
##    PageConfig = ORMAP_18x24MapConfig

#REFERENCE MAP DOCUMENT
document_name = "CURRENT"
document_name = os.path.join("C:/GeoModel/Clatsop/MapProduction18x24.mxd")
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
query = "%sMapNumber%s LIKE '%s'" % (delimiter_l, delimiter_r, mapnumber)
query = "[MapNumber] LIKE '8.10.25*'"
aprint(query)

mapindexrow = getrow(mxd, maindf, OrmapLayers.MAPINDEX_LAYER, query)
if not mapindexrow: eprint("Unable to read MapNumber \"%s\" in MapIndex feature class \"%s\"." % (mapnumber, OrmapLayers.MAPINDEX_LAYER))

pagelayoutrow = getrow(mxd, maindf, OrmapLayers.PAGELAYOUT_TABLE, query)
if not pagelayoutrow: eprint("Unable to load PageLayoutTable \"%s\"." % OrmapLayers.PAGELAYOUT_TABLE)

table_cancelled = getcancelled(mxd, maindf, OrmapLayers.CANCELLEDNUMBERS_TABLE, query)
if not len(table_cancelled): eprint("Unable to load CancelledNumbersTable \"%s\"." % OrmapLayers.CANCELLEDNUMBERS_TABLE)

defqueryrow = getrow(mxd, maindf, OrmapLayers.CUSTOMDEFINITIONQUERIES_TABLE, query)
if not defqueryrow: eprint("Unable to load optional DefCustomTable \"%s\"." % OrmapLayers.CUSTOMDEFINITIONQUERIES_TABLE)

aprint("Processing MapNumber '%s'." % mapnumber)

geom = mapindexrow[SHAPE]
extent = geom.extent
# Can I get the layer extent here instead of the feature
# since I just selected N features not just one?

#COLLECT MAP INDEX POLYGON INFORMATION AND GET FEATURE EXTENT

if not pagelayoutrow:
    #SET PAGE LAYOUT LOCATIONS FROM CONFIG
    aprint("Reading Page Layout items from Configuration File")
    DataFrameMinX = PageConfig.DataFrameMinX
    DataFrameMinY = PageConfig.DataFrameMinY
    DataFrameMaxX = PageConfig.DataFrameMaxX
    DataFrameMaxY = PageConfig.DataFrameMaxY
    mapExtent = extent
    MapAngle = PageConfig.MapAngle
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
    aprint("Reading Page Layout items from PAGELAYOUTTABLE")
    MapAngle = pagelayoutrow.MapAngle

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
if defqueryrow:

    #-- Items stored in long string input defQueryString field.  Pull them out and into their own array.
    defQueryList = defqueryrow.defQueryString.split(";")
    defQueryLayers = []
    defQueryValues = []

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
                sfixed = ""
                if qd:
                    sfixed = qd.replace("*MapNumber*", s_mapnum).replace("*MapScale*", s_mapscale)
                aprint("layername: %s was: \"%s\" query: \"%s\" replaced: \"%s\"" % (lyr.name, lyr.definitionQuery, qd, sfixed))
                lyr.definitionQuery = sfixed

            except KeyError:
                print("No need to touch this layer. \"%s\"" % lyr.name)

#PARSE ORMAP MAPNUMBER TO DEVELOP MAP TITLE
# example
# u'0408.00N10.00W25AD--0000'

orm = ormapnum()
orm.unpack(s_ormapnum)

shortmaptitle = "%2s %2s %2s" % (orm.township, orm.range, orm.section)
if orm.quarter != '0':
    shortmaptitle += orm.quarter
    if orm.quarterquarter != '0':  shortmaptitle += orm.quarterquarter
if s_cityname.strip():
    shortmaptitle += "\n" + s_cityname.replace(",","\n")

#CREATE TEXT FOR LONG MAP TITLE BASED ON SCALE FORMATS PROVIDED BY DOR.
longmaptitle = ""

scale   = "1\" = %d'" % (int(s_mapscale) / 12)

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
    if elm.name == "MainMapTitle":
        elm.text = longmaptitle
        elm.elementPositionX = TitleX
        elm.elementPositionY = TitleY
    if elm.name == "CountyName":
        elm.text = PageConfig.CountyName
        elm.elementPositionX = TitleX
        elm.elementPositionY = TitleY - CountyNameDist
    if elm.name == "MainMapScale":
        elm.text = scale
        elm.elementPositionX = TitleX
        elm.elementPositionY = TitleY - MapScaleDist

    if elm.name == "UpperLeftMapNum":
        elm.text = shortmaptitle
    if elm.name == "UpperRightMapNum":
        elm.text = shortmaptitle
        elm.elementPositionX = URCornerNumX
        elm.elementPositionY = URCornerNumY
    if elm.name == "LowerLeftMapNum":
        elm.text = shortmaptitle
    if elm.name == "LowerRightMapNum":
        elm.text = shortmaptitle
        elm.elementPositionX = LRCornerNumX
        elm.elementPositionY = LRCornerNumY

    if elm.name == "smallMapTitle":
        elm.text = longmaptitle
    if elm.name == "smallMapScale":
        elm.text = scale
    if elm.name == "PlotDate":
        now = datetime.datetime.now()
        elm.text = str("%d/%d/%d"%(now.month, now.day, now.year))
        elm.elementPositionX = DateX
        elm.elementPositionY = DateY
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

    if elm.name == "CanMapNumber":
        elm.text = " " #-- Important that this element has some text in it (event just a single space) so ArcMap does not "lose" it.
        cancelledElm2 = None
        try:
            cancelledElm2 = MAP.ListLayoutElements(mxd, "TEXT_ELEMENT", "CanMapNumber2")[0]
            cancelledElm2.text = " " #-- Important that this element has some text in it (event just a single space) so ArcMap does not "lose" it.
        except Exception as e:
            pass
        cancelledElm3 = None
        try:
            cancelledElm3 = MAP.ListLayoutElements(mxd, "TEXT_ELEMENT", "CanMapNumber3")[0]
            cancelledElm3.text = " " #-- Important that this element has some text in it (event just a single space) so ArcMap does not "lose" it.
        except Exception as e:
            pass
        n = 0
        maxRows = PageConfig.MaxCancelledRows

        if not cancelledrow:
            aprint(" ")
            aprint("------- WARNING -------")
            aprint("NO CANCELLED NUMBERS FOR THIS MAPNUMBER. IF THERE ARE SUPPOSED TO BE THEN MAKE SURE YOU DO NOT HAVE ANY RECORDS CURRENTLY SELECTED OR HAVE A DEFINITION QUERY SET ON YOUR CANCELLED NUMBERS TABLE.")
            aprint(" ")

        while cancelledrow:
            #-- If there is not a second text box for Cancelled Numbers force into the first text box.
            if n >= maxRows and cancelledElm2 == None:
                n = 0
            #-- If there is not a third text box for Cancelled Numbers force into the second text box.
            if n >= (maxRows*2) and cancelledElm2 != None and cancelledElm3 == None:
                n = maxRows

            if n < maxRows:
                elm.text += cancelledrow.Taxlot + "\n"
            elif n >= maxRows and n < (maxRows*2):
                cancelledElm2.text += cancelledrow.Taxlot + "\n"
            else:
                cancelledElm3.text += cancelledrow.Taxlot + "\n"

            n += 1
            cancelledrow = cancelledCursor.next()

        elm.text = PageConfig.CancelledNumberPrefix + "\n" + elm.text.strip() if elm.text != " " else " " #-- Important that this element has some text in it (event just a single space) so ArcMap does not "lose" it.
        elm.elementPositionX = CancelNumX
        elm.elementPositionY = CancelNumY
        if cancelledElm2 != None:
            cancelledElm2.text = cancelledElm2.text.strip() if cancelledElm2.text != " " else " " #-- Important that this element has some text in it (event just a single space) so ArcMap does not "lose" it.
            cancelledElm2.elementPositionX = elm.elementPositionX + cancelledElm2.elementWidth + .05
            cancelledElm2.elementPositionY = elm.elementPositionY
            if cancelledElm3 != None:
                cancelledElm3.text = cancelledElm3.text.strip() if cancelledElm3.text != " " else " " #-- Important that this element has some text in it (event just a single space) so ArcMap does not "lose" it.
                cancelledElm3.elementPositionX = cancelledElm2.elementPositionX + cancelledElm3.elementWidth + .05
                cancelledElm3.elementPositionY = elm.elementPositionY



#MODIFY MAIN DATAFRAME PROPERTIES
maindf.extent   = mapExtent
maindf.scale    = MapScale
maindf.rotation = MapAngle

#MODIFY LOCATOR DATAFRAME
if locatordf != None:
    mapIndexLayer = MAP.ListLayers(mxd, "MapIndex", locatordf)[0]
    locatorWhere = "MapNumber = '" + s_mapnum + "'"
    arcpy.management.SelectLayerByAttribute(mapIndexLayer, "NEW_SELECTION", locatorWhere)

#MODIFY SECTIONS DATAFRAME
if sectdf != None:
    sectionsLayer = MAP.ListLayers(mxd, "Sections_Select", sectdf)[0]
    sectionsLayer.definitionQuery = "[SectionNum] = " + str(sSection)

#MODIFY QUARTER SECTIONS DATAFRAME
if qSectdf != None:
    qSectionsLayer = MAP.ListLayers(mxd, "QtrSections_Select", qSectdf)[0]
    qSectionsLayer.definitionQuery = ""

    if sQtr == "A" and sQtrQtr == "0":
        qSectionsLayer.definitionQuery = "[QSectName] = 'A' or [QSectName]= 'AA' or [QSectName]= 'AB' or [QSectName]= 'AC' or [QSectName]= 'AD'"
    elif sQtr == "A" and sQtrQtr == "A":
        qSectionsLayer.definitionQuery = "[QSectName] = 'AA'"
    elif sQtr == "A" and sQtrQtr == "B":
        qSectionsLayer.definitionQuery = "[QSectName] = 'AB'"
    elif sQtr == "A" and sQtrQtr == "C":
        qSectionsLayer.definitionQuery = "[QSectName] = 'AC'"
    elif sQtr == "A" and sQtrQtr == "D":
        qSectionsLayer.definitionQuery = "[QSectName] = 'AD'"

    if sQtr == "B" and sQtrQtr == "0":
        qSectionsLayer.definitionQuery = "[QSectName] = 'B' or [QSectName]= 'BA' or [QSectName]= 'BB' or [QSectName]= 'BC' or [QSectName]= 'BD'"
    elif sQtr == "B" and sQtrQtr == "A":
        qSectionsLayer.definitionQuery = "[QSectName] = 'BA'"
    elif sQtr == "B" and sQtrQtr == "B":
        qSectionsLayer.definitionQuery = "[QSectName] = 'BB'"
    elif sQtr == "B" and sQtrQtr == "C":
        qSectionsLayer.definitionQuery = "[QSectName] = 'BC'"
    elif sQtr == "B" and sQtrQtr == "D":
        qSectionsLayer.definitionQuery = "[QSectName] = 'BD'"

    if sQtr == "C" and sQtrQtr == "0":
        qSectionsLayer.definitionQuery = "[QSectName] = 'C' or [QSectName]= 'CA' or [QSectName]= 'CB' or [QSectName]= 'CC' or [QSectName]= 'CD'"
    elif sQtr == "C" and sQtrQtr == "A":
        qSectionsLayer.definitionQuery = "[QSectName] = 'CA'"
    elif sQtr == "C" and sQtrQtr == "B":
        qSectionsLayer.definitionQuery = "[QSectName] = 'CB'"
    elif sQtr == "C" and sQtrQtr == "C":
        qSectionsLayer.definitionQuery = "[QSectName] = 'CC'"
    elif sQtr == "C" and sQtrQtr == "D":
        qSectionsLayer.definitionQuery = "[QSectName] = 'CD'"

    if sQtr == "D" and sQtrQtr == "0":
        qSectionsLayer.definitionQuery = "[QSectName] = 'D' or [QSectName]= 'DA' or [QSectName]= 'DB' or [QSectName]= 'DC' or [QSectName]= 'DD'"
    elif sQtr == "D" and sQtrQtr == "A":
        qSectionsLayer.definitionQuery = "[QSectName] = 'DA'"
    elif sQtr == "D" and sQtrQtr == "B":
        qSectionsLayer.definitionQuery = "[QSectName] = 'DB'"
    elif sQtr == "D" and sQtrQtr == "C":
        qSectionsLayer.definitionQuery = "[QSectName] = 'DC'"
    elif sQtr == "D" and sQtrQtr == "D":
        qSectionsLayer.definitionQuery = "[QSectName] = 'DD'"

arcpy.RefreshActiveView()

# That's all, folks!
    
