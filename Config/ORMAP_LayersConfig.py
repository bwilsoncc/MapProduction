# ---------------------------------------------------------------------------
# ORMAP_LayersConfig.py
# Created by: Shad Campbell
# Date: 3/11/2011
# Updated by: Brian Wilson for Clatsop County 12/12/2017
# Description: This is a configuration file to be customized by each county.
# Do not delete any of the items in this file.  If they are not in use then
# specify their value and/or definition query to "".
# ---------------------------------------------------------------------------

# Clatsop County
# 2017-12-11 -- Brian converted this file from GeoModel/Clatsop/MapProduction18x24.ini

# *MapNumber* will be replaced with the value of MapNumber from the associated feature class
# *MapScale* will be replaced with the value of MapScale from the feature class

# Using the right delimiters "[" "]" in this case is necessary because
# ESRI and or Microsoft change it according to the database type!
# You probably will have to change it if you switch to a newer geodatabase.

__base_qd  = "([MapNumber]='{0}' OR [MapNumber] IS NULL OR [MapNumber]='')" 
# The variables "mapnumber" and "mapscale" are defined in the zoomToMapNumber.py script and get eval'ed in.
DEFAULT_QD = "\"" + __base_qd + "\".format(mapnumber)"
ANNO_QD    = "\"" + __base_qd + " AND ([MapScale]={1} OR [MapScale]={1}/12)\".format(mapnumber, mapscale)"

# LineType
#  8  Public road ROW
# 14  Railroad ROW 
# 32  Parcel boundary
# 51  Detail Map Boundary
# 52  Detail Map Boundary

# For MDB and shapefiles the case of field names does not matter.
MapNumberField = "MapNumber"
ORMapNumberField = "OrMapNum"

##### MAIN DATA FRAME #####

MainDF = "MapView"
MainLayers=[
    ("MapIndex",           "\"[OrMapNum] =  '{0}'\".format(orm.ormapnumber)"),
    ("MapIndex - SeeMaps", "\"[OrMapNum] <> '{0}'\".format(orm.ormapnumber)"),
    ("MapIndex - Mask",    "\"[OrMapNum] <> '{0}'\".format(orm.ormapnumber)"),

    ("LotsAnno",         ANNO_QD),
    ("PlatsAnno",        ANNO_QD),
    ("TaxCodeAnno",      ANNO_QD),
    ("TaxlotAnno",       ANNO_QD),
    ("AcresAnno",        ANNO_QD),
    ("Anno0010scale",    ANNO_QD),        
    ("Anno0020scale",    ANNO_QD),        
    ("Anno0030scale",    ANNO_QD),        
    ("Anno0040scale",    ANNO_QD),        
    ("Anno0050scale",    ANNO_QD),        
    ("Anno0100scale",    ANNO_QD),        
    ("Anno0200scale",    ANNO_QD),        
    ("Anno0400scale",    ANNO_QD),        
    ("Anno0800scale",    ANNO_QD),        
    ("Anno2000scale",    ANNO_QD),        

    # Setting the query to "" means you want to clear any definition query that might be set in the MXD.
    # If you don't want a layer's query ERASED then don't list it with a query of "".
    
    ('PLSSLines - Above',         '"[LineType]=44 AND [MapScale]={0}".format(mapscale)'),
#   ("Corner - Above",            ""),
#   ("TaxCodeLines - Above",      ""),
    ("TaxlotLines - Above",       '"[LineType] = 8 or [LineType] = 14 or [LineType] = 51 or [LineType] = 52"'),
#   ("ReferenceLines - Above",    ""),
#   ("CartographicLines - Above", ""),
#   ("WaterLines - Above",        ""),
#   ("Water - Above",             '"[WaterType]<>\'Land\'"')

#   ("Corner - Below",            ""),
#   ("TaxCodeLines - Below",      ""),
#   ("TaxlotLines - Below",       ""),
#   ("ReferenceLines - Below",    ""),
#   ("CartographicLines - Below", ""),
#   ("WaterLines - Below",        ""),
#    ("Water",                    '"[WaterType]<>\'Land\'"'),
]
MapIndexLayer = MainLayers[0]

PAGELAYOUT_TABLE="PageLayoutElements"
CUSTOMDEFINITIONQUERIES_TABLE="CustomDefinitionQueries"

##### locator map data frame #####
LocatorDF = "LocatorDF"
LocatorScale = None
LocatorLayers=[
        ("MapIndex TR Highlight", "\"[TRlabel]='{0}{1}{2}{3}'\".format(int(orm.township), orm.township_dir, int(orm.range), orm.range_dir)"),
        ]
LocatorExtentLayer = None # Don't pan this locator map. It shows the whole county.

##### Sections map data frame #####
SectionDF = "SectionsDF"
SectionScale = 180000
SectionLayers=[
        ("MapIndex TR Outline", "\"[TRlabel]='{0}{1}{2}{3}'\".format(int(orm.township), orm.township_dir, int(orm.range), orm.range_dir)"),
        
        # SHAPEFILE!!!
        ("Section - Highlight", '"\\"SECTION\\" = \'{0}\'".format(orm.section)'),
        ("Sections",        '"\\"TR\\" =  \'{0}{1}{2}{3}\'\".format(int(orm.township), orm.township_dir, int(orm.range), orm.range_dir)'),
        ("Sections - Mask", '"\\"TR\\" <> \'{0}{1}{2}{3}\'\".format(int(orm.township), orm.township_dir, int(orm.range), orm.range_dir)'),
        ]
SectionExtentLayer = SectionLayers[0][0]

##### Quarter sections map data frame #####
QSectionDF = "QSectionsDF"
QSectionScale = 48000
QSectionLayers=[
        ("MapIndex QSection Highlight", "\"[OrMapNum]='{0}'\".format(orm.ormapnumber)"),
        
        # SHAPEFILE!!!
        ("Sections - Mask", '"\\"SECTION\\" <> \'{0}\'".format(orm.section)'),
        ("Section",         '"\\"SECTION\\" =  \'{0}\'".format(orm.section)'),
        ]
QSectionExtentLayer = QSectionLayers[0][0]

CancelledNumbersTable = "K:/taxmaped/Clatsop/towned/cancelled.xlsx"


