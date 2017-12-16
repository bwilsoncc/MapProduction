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

##### MAIN DATA FRAME #####

MainDF = "MapView"

LOTSANNO_LAYER="LotsAnno"
LOTSANNO_QD="[MapNumber] = '*MapNumber*' OR [MapNumber] is NULL OR [MapNumber] = ''"

PLATSANNO_LAYER="PlatsAnno"
PLATSANNO_QD="[MapNumber] = '*MapNumber*' OR [MapNumber] is NULL OR [MapNumber] = ''"

TAXCODEANNO_LAYER="TaxCodeAnno"
TAXCODEANNO_QD="[MapNumber] = '*MapNumber*' OR [MapNumber] is NULL OR [MapNumber] = ''"

TAXNUMANNO_LAYER="TaxlotNumberAnno"
TAXNUMANNO_QD="[MapNumber] = '*MapNumber*' OR [MapNumber] is NULL OR [MapNumber] = ''"

ACRESANNO_LAYER="TaxlotAcresAnno"
ACRESANNO_QD="[MapNumber] = '*MapNumber*' OR [MapNumber] is NULL OR [MapNumber] = ''"

ANNO10_LAYER="Anno0010scale"
ANNO10_QD="[MapNumber] = '*MapNumber*' OR [MapNumber] is NULL OR [MapNumber] = ''"

ANNO20_LAYER="Anno0020scale"
ANNO20_QD="[MapNumber] = '*MapNumber*' OR [MapNumber] is NULL OR [MapNumber] = ''"

ANNO30_LAYER="Anno0030scale"
ANNO30_QD="[MapNumber] = '*MapNumber*' OR [MapNumber] is NULL OR [MapNumber] = ''"

ANNO40_LAYER="Anno0040scale"
ANNO40_QD="[MapNumber] = '*MapNumber*' OR [MapNumber] is NULL OR [MapNumber] = ''"

ANNO50_LAYER="Anno0050scale"
ANNO50_QD="[MapNumber] = '*MapNumber*' OR [MapNumber] is NULL OR [MapNumber] = ''"

ANNO60_LAYER="Anno0060scale"
ANNO60_QD="[MapNumber] = '*MapNumber*' OR [MapNumber] is NULL OR [MapNumber] = ''"

ANNO100_LAYER="Anno0100scale"
ANNO100_QD="[MapNumber] = '*MapNumber*' OR [MapNumber] is NULL OR [MapNumber] = ''"

ANNO200_LAYER="Anno0200scale"
ANNO200_QD="[MapNumber] = '*MapNumber*' OR [MapNumber] is NULL OR [MapNumber] = ''"

ANNO400_LAYER="Anno0400scale"
ANNO400_QD="[MapNumber] = '*MapNumber*' OR [MapNumber] is NULL OR [MapNumber] = ''"

ANNO800_LAYER="Anno0800scale"
ANNO800_QD="[MapNumber] = '*MapNumber*' OR [MapNumber] is NULL OR [MapNumber] = ''"

ANNO2000_LAYER="Anno2000scale"
ANNO2000_QD="[MapNumber]='*MapNumber*' OR [MapNumber] is NULL OR [MapNumber] = ''"

CORNER_ABOVE_LAYER="Corner - Above"
CORNER_ABOVE_QD=""

TAXCODELINES_ABOVE_LAYER="TaxCodeLines - Above"
TAXCODELINES_ABOVE_QD=""

TAXLOTLINES_ABOVE_LAYER="TaxlotLines - Above"
TAXLOTLINES_ABOVE_QD="[LineType] = 8 or [LineType] = 14 or [LineType] = 51 or [LineType] = 52"

REFLINES_ABOVE_LAYER="ReferenceLines - Above"
REFLINES_ABOVE_QD=""

CARTOLINES_ABOVE_LAYER="CartographicLines - Above"
CARTOLINES_ABOVE_QD=""

WATERLINES_ABOVE_LAYER="WaterLines - Above"
WATERLINES_ABOVE_QD=""

WATER_ABOVE_LAYER="Water - Above"
WATER_ABOVE_QD=""

MAPINDEXSEEMAP_LAYER="MapIndex - SeeMaps"
MAPINDEXSEEMAP_QD=""

MAPINDEX_LAYER="MapIndex - SeeMaps"
MAPINDEX_QD="[MapNumber] = '*MapNumber*'"

MAPINDEXMASK_LAYER="MapIndex - Mask"
MAPINDEXMASK_QD="[MapNumber] <> '*MapNumber*' OR [MapNumber] is NULL OR [MapNumber] = ''"

CORNER_BELOW_LAYER="Corner - Below"
CORNER_BELOW_QD=""

TAXCODELINES_BELOW_LAYER="TaxCodeLines - Below"
TAXCODELINES_BELOW_QD=""

TAXLOTLINES_BELOW_LAYER="TaxlotLines - Below"
TAXLOTLINES_BELOW_QD=""

REFLINES_BELOW_LAYER="ReferenceLines - Below"
REFLINES_BELOW_QD=""

CARTOLINES_BELOW_LAYER="CartographicLines - Below"
CARTOLINES_BELOW_QD=""

WATERLINES_BELOW_LAYER="WaterLines - Below"
WATERLINES_BELOW_QD=""

WATER_BELOW_LAYER="Water - Below"
WATER_BELOW_QD=""

PAGELAYOUT_TABLE="PageLayoutElements"
CANCELLEDNUMBERS_TABLE="CancelledNumbers"
CUSTOMDEFINITIONQUERIES_TABLE="CustomDefinitionQueries"

# You can define up to 20 "extra" layers. Just number them like this.
EXTRA1_LAYER="ExtraLayer1"
EXTRA1_QD=""

##### locator map data frame #####
LocatorDF = "LocatorDF"
LOCATOR_LAYER="Highlight - MapIndex"
LOCATOR_QD="[TR] = '%02d%02d%s'"

##### Sections map data frame #####
SectionsDF = "SectionsDF"
SECTIONS_LAYER="Highlight - Sections"
SECTIONS_QD="[SectionNum] = %s" # This is an integer so don't wrap in quotes.

##### Quarter sections map data frame #####
QSectionsDF = "QSectionsDF"
QTRSECTIONS_LAYER="Highlight - QtrSections"
QSECTIONS_QD="[QSectName] = '%s'"
