# ---------------------------------------------------------------------------
# ORMAP_LayersConfig.py
# Created by: Shad Campbell
# Date: 3/11/2011
# Updated by: Brian Wilson for Clatsop County 12/12/2017
# Description: This is a configuration file to be customized by each county.
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

MapNumberField = "MapNumber"
ORMapNumberField = "OrMapNum"

##### MAIN DATA FRAME #####

MainDF = "MapView"
MainLayers=[
    ("MapIndex",           "\"[OrMapNum] =  '{0}'\".format(orm.ormapnumber)"),
#    ("MapIndex - SeeMaps", "\"[OrMapNum] <> '{0}'\".format(orm.ormapnumber)"),
#    ("MapIndex - Mask",    "\"[OrMapNum] <> '{0}'\".format(orm.ormapnumber)"),

    # Setting the query to "" means you want to clear any definition query that might be set in the MXD.
    # If you don't want a layer's query ERASED then don't list it with a query of "".
    
#   ("Corner - Above",            ""),
#   ("TaxCodeLines - Above",      ""),
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

##### locator map data frame #####
LocatorDF = "LocatorDF"
LocatorScale = 800000
LocatorLayers=[
        ("Township - highlight",  
         '"TR=\'{0}{1}{2}{3}\'".format(int(orm.township), orm.township_dir, int(orm.range), orm.range_dir)'),

        ("Township",  
         '"TR<>\'{0}{1}{2}{3}\'".format(int(orm.township), orm.township_dir, int(orm.range), orm.range_dir)'),
        ]
LocatorExtentLayer = None # Don't pan this locator map. It always shows the whole county.
LocatorFeatureCount = None

##### Sections map data frame #####
SectionDF = "SectionsDF"
SectionScale = 180000
SectionLayers=[
        ("Section - highlight",
        '"TOWN = \'{0}\' AND RANGE = \'{1}\' AND SECTION = \'{2}\'".format(orm.township, orm.range, orm.section)'
        ),
  
         ("Sections",'"TOWN = \'{0}\' AND RANGE = \'{1}\'".format(orm.township, orm.range)'
        ),
        ]
# Pan locator map to this selection
SectionExtentLayer = SectionLayers[1][0]
SectionFeatureCount = SectionLayers[0][0]

##### Quarter sections map data frame #####
QSectionDF = "QSectionsDF"
QSectionScale = 50000
QSectionLayers=[
        ('Section',
             '"TOWN = \'{0}\' AND RANGE = \'{1}\' AND SECTION = \'{2}\'".format(orm.township, orm.range, orm.section)'),
        ('Sections - background',
        '"NOT (TOWN = \'{0}\' AND RANGE = \'{1}\' AND SECTION = \'{2}\')".format(orm.township, orm.range, orm.section)'),
        ]
# Pan locator map to this selection
QSectionExtentLayer = QSectionLayers[0][0]
QSectionFeatureCount = QSectionLayers[0][0]

CancelledNumbersTable = "K:/taxmaped/Clatsop/towned/cancelled.xlsx"


