# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------------
# convert_to_geodatabase.py
# Created on: 2018-01-10 15:29:52.00000
# Description:
# Convert coverages to geodatabase feature classes
# Usage: convert_to_geodatabase.py coverage_folder geodatabase
# ---------------------------------------------------------------------------
from __future__ import print_function
import arcpy
import sys, os
from Toolbox.arc_utilities import aprint, eprint

# ========================================================================

def import_features(coverage, fc):
    """ Import a coverage into a geodatabase feature class.

    This is done by first deleting any features in the database
    and then appending to the class.
    I think this is done to keep the new schema?
    It does mean the output feature class has to exist. """

    if not arcpy.Exists(coverage):
        eprint("Input coverage must exist. %s" % coverage)
        return False
    
    if not arcpy.Exists(fc):
        eprint("Output feature class must exist. %s" % fc)
        return False
    
    aprint("Importing %s to %s." % (coverage,fc))
    arcpy.DeleteFeatures_management(fc)
    arcpy.Append_management(coverage, fc, "NO_TEST")

    return True

def import_all(source_folder, geodatabase):

    # First item is coverage name, second is featureclass name
    table_xlat = [
        ("mapindex\\polygon", "TaxlotsFD\\MapIndex",      "MapScale"),

        ("cartolin\\arc",     "CartographicLines",        None),
        ("corner\\point",     "Corner",                   None),
        ("plssline\\arc",     "PLSSLines",                None),
        ("refline\\arc",      "ReferenceLines",           None),
        ("taxcode\\arc",      "TaxlotsFD\\TaxCodeLines",  None),
        ("taxcode\\polygon",  "TaxlotsFD\TaxCode",        None),
        ("taxlot\\arc",       "TaxlotsFD\\TaxlotLines",   None),
        ("taxlot\\polygon",   "TaxlotsFD\\Taxlot",        None),
        ("waterlin\\arc",     "Waterlines",               None),
        ("water\\polygon",    "Water",                    None),
    ]

    start    = 0
    maxcount = len(table_xlat)
    step     = 1
    
    arcpy.SetProgressor("step", "Importing %d coverages." % maxcount, start, maxcount, step)

    t = 0
    for coverage,fc,fieldname in table_xlat:
        msg = "Importing %s to %s." % (coverage, fc)
        arcpy.SetProgressorLabel(msg)
        t += 1
        #print("%d/%d" % (t, maxcount), msg)

        srccvg = os.path.join(source_folder, coverage)        
        destfc = os.path.join(geodatabase, fc)
        if not import_features(srccvg, destfc):
            return False
        if fieldname:
            # I wonder which feature classes I should really do this for.
            aprint("Recalculating %s in %s." % (fieldname,fc))
            arcpy.CalculateField_management(destfc, fieldname, "!%s!*12" % fieldname, "PYTHON")
        arcpy.SetProgressorPosition(t)

    return True

# ========================================================================
        
if __name__ == "__main__":

    try:
        sourcedir = sys.argv[1]
    except:
        sourcedir = "C:\\GeoModel\\Clatsop\\Workfolder"

    try:
        geodatabase = sys.argv(2)
    except:
        geodatabase = "C:\\GeoModel\\Clatsop\\ORMAP-SchemaN_08-21-08.mdb"

    import_all(sourcedir, geodatabase)
    
    print("Tests completed.")

# That's all!
