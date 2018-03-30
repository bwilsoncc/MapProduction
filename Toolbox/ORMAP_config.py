# ORMAP_config.py
# Clatsop County
# 2018-03-30 -- folded in the two config files, layout and map
# 2017-12-11 -- Brian converted this file from MapProduction18x24.ini (then deleted 95% of it!)

##### Locator map data frame #####
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
        '"TOWN = \'{0}\' AND RANGE = \'{1}\' AND SECTION = \'{2}\'".format(orm.township, orm.range, orm.section)'),
         ("Sections",'"TOWN = \'{0}\' AND RANGE = \'{1}\'".format(orm.township, orm.range)'),
        ]
# Pan locator map to this selection
SectionExtentLayer = SectionLayers[1][0]

# If there are no features showing (due to query definition) then hide this locator map
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

# If there are no features showing (due to query definition) then hide this locator map
QSectionFeatureCount = QSectionLayers[0][0]

# ---------------------------------------------------------------------------
# Cancelled Taxlot Numbers appear in a table with the numbers sorted
# vertically. The elements in the table are a title and several columns.
#
# Note if you "ungroup" the elements in arcmap and then regroup them
# you will have to reset the name on the group.

CancelledNumbersTable = "K:/taxmaped/Clatsop/towned/cancelled.xlsx"
MaxCancelledRows = 15 # Go to 8 point font if # of rows exceeds this

