# -*- coding: utf-8 -*-
"""
convert_to_geodatabase.py
Created on: 2018-01-10 15:29:52.00000
Description: Convert coverages features to geodatabase feature classes
@author: Brian Wilson <bwilson@co.clatsop.or.us>
"""
from __future__ import print_function
import arcpy
import os, logging
import re
from Toolbox.arc_utilities import ListFieldNames, DeleteFC, AddField
from ormapnum import ormapnum

# ========================================================================

def import_features(coverage, fc):
    """ Import a coverage into a geodatabase feature class.
    The output feature class has to exist. """

    logging.info("import_features(%s, %s)" % (coverage,fc))
    rval = False

    if not arcpy.Exists(coverage):
        logging.error("Input coverage must exist. %s" % coverage)
    elif not arcpy.Exists(fc):
        logging.error("Output feature class must exist. %s" % fc)
    else:   
        try:
            arcpy.Append_management(coverage, fc, "NO_TEST")
        except Exception as e:
            logging.error("import_features(%s,%s) Append :%s" % (coverage,fc, e))
        rval = True

    return rval

def import_all_features(source_folder, geodatabase):

    # First item is coverage name, second is featureclass name
    # DON'T forget, attributes won't be in the output featureclass unless they are in the template database.

    table_xlat = [
        ("tmpcorner\\point",     "corner",                     "MapScale"), #

#       ("tmptaxlot\\polygon",   "taxlots_fd\\taxlot",          None),       # polygons are generated by make_polygons
        ("tmptaxlot\\arc",       "taxlots_fd\\taxlot_lines",    None),       # geometry source
        ("tmptaxlot\\label",     "taxlots_fd\\taxlot_points",   None),       # attribute source

#       ("tmptaxcode\\polygon",  "taxlots_fd\\taxcode",         None),       # polygons are generated by make_polygons
        ("tmptaxcode\\arc",      "taxlots_fd\\taxcode_lines",   None),       # geometry source
        ("tmptaxcode\\label",    "taxlots_fd\\taxcode_points",  None),       # attribute source
        
#       ("tmptaxbound\\polygon", "taxlots_fd\\mapindex",        "MapScale"), # polygons are generated by make_polygons
        ("tmptaxbound\\arc",     "taxlots_fd\\mapindex_lines",  None),       # geometry source
        ("tmptaxbound\\label",   "taxlots_fd\\mapindex_points", None),       # attribute source

        ("tmpwaterl\\arc",     "water_lines",                "MapScale"),
#       ("tmpwater\\polygon",    "Water",                      None),       # needed??

        ("tmpcartol\\arc",     "cartographic_lines",        "MapScale"),
        ("tmprefl\\arc",      "reference_lines",           "MapScale"),
        ("tmpplssl\\arc",     "plss_lines",                "MapScale"),
    ]

    start    = 0
    maxcount = len(table_xlat)
    step     = 1
    
    t = 0
    for coverage,fc,fieldname in table_xlat:
        t += 1

        srccvg = os.path.join(source_folder, coverage)        
        destfc = os.path.join(geodatabase, fc)

        import_features(srccvg, destfc)
            
    return True

def make_polygons(infc, labelfc, outfc):
    """ Create polygons from a feature class.
    infc      input feature class (can be lines or polygons)
    labelfc   point feature class containing attributes for outfc
    outfc     where to write polygons """

    # Notes on "FeatureToPolygon"
    # If you use the "NO ATTRIBUTES" default, then only the shapes are move from the input to the generated polygon feature class.
    # If you use "ATTRIBUTES" the attributes are copied.
    # If you use "ATTRIBUTES" and a polygon or line feature class AND a point feature class,
    #   the attributes from the points are copied to the output (the poly/line attributes are lost). 
    # If there are multiple points inside a new polygon feature it picks attributes from one randomly. 
    # Input features can be lines or polygons, so you can think of it as a way of just transferring the attributes if you have input polygons.
    # The blank "" arg is a tolerance, if you have sloppy input you can use this to close the polygons.
    #
    # NB when I ran it as a standalone tool in ArcMap I got a background server error, I had to run it in foreground.

    # I wish that ESRI was a bit more consistent in what DOES and DOES NOT support the workspace environment variable.
    ws = str(arcpy.env.workspace)
    
    logging.info("make_polygons(%s, %s, %s)" % (infc, labelfc, outfc))
    i = os.path.join(ws, infc)
    l = os.path.join(ws, labelfc)
    o = os.path.join(ws, outfc) 
    
    try:
        arcpy.Delete_management(o)
    except Exception as e:
        logging.info("Did not delete %s, %s" % (o, e))
    try:
        arcpy.FeatureToPolygon_management(i, o, "", "ATTRIBUTES", l)
    except Exception as e:
        logging.error(e)

    return

def update_mapindex(fc):
    """ Update the mapindex fc by adding and populating shortmaptitle and longmaptitle fields.
    longmaptitle  a string that can be used on maps as the "small map title"
    """
    if arcpy.Exists(fc):
        AddField(fc, "ShortMapTitle", "TEXT", fieldlen=20)
        AddField(fc, "LongMapTitle", "TEXT", fieldlen=50)

        orm = ormapnum()

        fields = ["ORMapNum", "ShortMapTitle", "LongMapTitle", "OID@"]
        ORMAPNUM = 0
        SHORTTTL = 1
        LONGTTL  = 2
        OID      = 3

        with arcpy.da.UpdateCursor(fc, fields) as cursor:
            for row in cursor:
                oid = row[OID]
                o   = row[ORMAPNUM]
                if not o:
                    logging.debug("Deleting empty feature %d in %s" % (oid, fc))
                    cursor.deleteRow()
                else:
                    try:
                        orm.unpack(o)
                        row[SHORTTTL] = orm.shortmaptitle
                        row[LONGTTL]  = orm.longmaptitle
                    except ValueError as e:
                        logging.warn(e)

                    cursor.updateRow(row)
    return

__stdscales = {
          10 :   120,
          20 :   240,
          30 :   360,
          40 :   480,
          50 :   600,
          60 :   720, 
         100 :  1200,
         200 :  2400,
         400 :  4800,
         800 :  9600,
        1000 : 12000,
        2000 : 24000}

def fix_mapacres(fc):
    """ The field mapacres needs to be filled in with acres. """
    logging.info("Calculating MapAcres in %s" % fc)
    arcpy.CalculateField_management(fc, "MapAcres", "!SHAPE.AREA@ACRES!", "PYTHON")
    return

def fixmapscale(fc):
    """ Fix the values of a mapscale column, if they are not already correct. 
    Returns number of rows updated. """
    # Since this only changes known ":' scales to relative scales,
    # it can be run over and over and it won't hurt anything.
    
    count = 0

    if not arcpy.Exists(fc) or int(arcpy.GetCount_management(fc).getOutput(0)) == 0:
        logging.debug("fixmapscale(%s) No features" % fc)
        return
    d = arcpy.Describe(fc)
    try:
        if d.featureType != "Simple":
            return 0
    except Exception as e:
        logging.error("fix_mapscale(%s): %s" % (fc,e))
        return 0

    fieldnames = ListFieldNames(fc)
    try:
        i = [s.lower() for s in fieldnames].index('mapscale')
        f = fieldnames[i]
    except ValueError:
        return 0

    logging.info("Recalculating %s in %s." % (f,fc))
    with arcpy.da.UpdateCursor(fc, [f]) as cursor:
        for row in cursor:
            try:
                newscale = __stdscales[row[0]]
                row[0] = newscale
                cursor.updateRow(row)
                count += 1
            except KeyError:
                continue # Probably does not need updating

    logging.debug("fixmapscale(%s): %d rows updated" % (fc, count))
    return count

def fix_mapscales(fclist):
    """ Fix the "mapscale" field in a list of feature classes. 
        arcpy.env.workspace has to be set to the geodatabase. """

    for fc in arcpy.ListFeatureClasses():
        if fc in fclist:  # Only do the ones in this list
            fixmapscale(fc)

    return

def fixlinetype(fc):
    """ Fix the value of linetype column.
    Returns number of rows updated. """

#    In a more perfect world this field would be correct when transferred from coverages
#    but I find AML to be to confusing!
    
    count = 0

    if not arcpy.Exists(fc) or int(arcpy.GetCount_management(fc).getOutput(0)) == 0:
        logging.debug("fixlinetype(%s) No features" % fc)
        return
    d = arcpy.Describe(fc)
    try:
        if d.featureType != "Simple":
            return 0
    except Exception as e:
        logging.error("fixlinetype(%s): %s" % (fc,e))
        return 0

    fieldnames = ListFieldNames(fc)
    try:
        i = [s.lower() for s in fieldnames].index('linetype')
        f = fieldnames[i]
    except ValueError:
        return 0

    logging.info("Setting %s in %s." % (f,fc))
    with arcpy.da.UpdateCursor(fc, [f, 'taxlot']) as cursor:
        for row in cursor:
            if row[1] == 'ROAD':
                lt = 8
            elif row[1] == 'RAIL':
                lt = 14
            else:
                lt = 32
            row[0] = lt
            cursor.updateRow(row)
            count += 1

    return count


def fix_linetypes(fclist):
    """ Fix the "linetype" field in a list of feature classes. 
        arcpy.env.workspace has to be set to the geodatabase. """

    for fc in arcpy.ListFeatureClasses():
        if fc in fclist:  # Only do the ones in this list
            fixlinetype(fc)
    return

# ========================================================================
        
if __name__ == "__main__":

    workfolder = "C:\\GeoModel\\Clatsop\\Workfolder"
    target = "t6-10"
    
    sourcedir = os.path.join(workfolder, target)
    geodatabase = os.path.join(workfolder, "ORMAP_Clatsop.gdb")

    print("Importing features...")
    import_all_features(sourcedir, geodatabase)

    saved = arcpy.env.workspace
    arcpy.env.workspace = os.path.join(geodatabase, "taxlots_fd")

    make_polygons("mapindex_lines", "mapindex_points", "mapindex")
    make_polygons("taxcode_lines",  "taxcode_points",  "taxcode")
    make_polygons("taxlot_lines",   "taxlot_points",   "taxlot")

    update_mapindex("mapindex")

    fix_mapscales(["mapindex"])
    fix_acres("taxlot")
    fix_linetypes(["taxlot"])

    arcpy.env.workspace = saved

    print("coverage_to_geodatabase tests completed.")

# That's all!
