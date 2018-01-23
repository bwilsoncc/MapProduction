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
import os
import logging
from Toolbox.arc_utilities import aprint, eprint, deletefc

# ========================================================================

def import_features(coverage, fc):
    """ Import a coverage into a geodatabase feature class.

    This is done by first deleting any features in the database
    and then appending to the class.
    I think this is done to keep the new schema?
    It does mean the output feature class has to exist. """

    if not arcpy.Exists(coverage):
        msg = "Input coverage must exist. %s" % coverage
        eprint(msg)
        logging.error(msg)
        return False
    
    if not arcpy.Exists(fc):
        msg = "Output feature class must exist. %s" % fc
        eprint(msg)
        logging.error(msg)
        return False
    
    try:
        temp = "annofeatureslayer"
        arcpy.MakeFeatureLayer_management(fc, temp)
        arcpy.SelectLayerByAttribute_management(temp, "NEW_SELECTION")
        featcount = int(arcpy.GetCount_management(temp).getOutput(0)) 
        if featcount > 0:
            arcpy.DeleteFeatures_management(temp)
        arcpy.Append_management(coverage, fc, "NO_TEST")
    except Exception as e:
        logging.error("import_features(%s,%s):%s" % (coverage,fc, e))
        
    return True

def import_all_features(source_folder, geodatabase):

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

        aprint("Importing %s to %s." % (coverage,fc))
        if not import_features(srccvg, destfc):
            continue
        
        if fieldname:
            # I wonder which feature classes I should really do this for.
            aprint("Recalculating %s in %s." % (fieldname,fc))
            arcpy.CalculateField_management(destfc, fieldname, "!%s!*12" % fieldname, "PYTHON")
        
        arcpy.SetProgressorPosition(t)

    return True

# ---------------------------------------------------------------------------

def fix_fontsize(outputfc):
    aprint("fix_fontsize(%s)" % outputfc)
    arcpy.CalculateField_management(outputfc, "FontSize", "!MAPSIZE!", "PYTHON", "")

def fix_caret(outputfc):
    aprint("fix_caret(%s)" % outputfc)
    arcpy.CalculateField_management(outputfc, "TEXT_",      "!TEXT_!.replace('^',u'\xb0')",      "PYTHON", "")
    arcpy.CalculateField_management(outputfc, "TextString", "!TextString!.replace('^',u'\xb0')", "PYTHON", "")
    return True

# Read all the details
# http://desktop.arcgis.com/en/arcmap/latest/tools/conversion-toolbox/import-coverage-annotation.htm

def import_anno(annolayer, outputfc, linkedfc, reference_scale):
    success = True 

    annocount = int(arcpy.GetCount_management(annolayer).getOutput(0))
    if annocount <= 0:
        aprint("No annotation to import in \"%s\"." % annolayer)
        return False
    
    aprint("Importing \"%s\" to \"%s\" Linked FC: \"%s\"" % (annolayer.name, outputfc, linkedfc)) 
    linked = "STANDARD"
    if linkedfc: linked = "FEATURE_LINKED" 
    try:  
        arcpy.ImportCoverageAnnotation_conversion(annolayer, outputfc, reference_scale, 
                                                  "CLASSES_FROM_LEVELS", "NO_MATCH", "NO_SYMBOL_REQUIRED", 
                                                  linked, linkedfc,
                                                  "AUTO_CREATE", "AUTO_UPDATE")
    except Exception as e:
        msg = "import_anno(%s, %s, %s, %s), \"%s\"" % (annolayer, outputfc, linkedfc, reference_scale, e)
        aprint(msg)
        logging.error(msg)
        success = False
        
    return success
    
def convert_anno(mxd, destination, reference_scale, overwrite):
    """ Convert coverage annotation to feature class annotation. """
        
    warning = 0
    
    # Assumption is that there is only one dataframe in the annotation mxd.
    df = arcpy.mapping.ListDataFrames(mxd)[0]

    linklist = [   # (Layer name, output featureclass, featurelinked_fc)
                ("StdAnno.igds 10 scale",   "Anno0010scale",    ""),
                ("StdAnno.igds 20 scale",   "Anno0020scale",    ""),
                ("StdAnno.igds 30 scale",   "Anno0030scale",    ""),
                ("StdAnno.igds 40 scale",   "Anno0040scale",    ""),
                ("StdAnno.igds 50 scale",   "Anno0050scale",    ""),
                ("StdAnno.igds 100 scale",  "Anno0100scale",    ""),
                ("StdAnno.igds 200 scale",  "Anno0200scale",    ""),
                ("StdAnno.igds 400 scale",  "Anno0400scale",    ""),
                ("StdAnno.igds 800 scale",  "Anno0800scale",    ""),
                ("StdAnno.igds 2000 scale", "Anno2000scale",    ""),
                
                ("FLAnno.igds TaxlotNum",   "TaxlotsFD/TaxlotNumberAnno",  "TaxlotsFD/Taxlot"     ),
                ("FLAnno.igds Code",        "TaxlotsFD/TaxCodeAnno",       "TaxlotsFD/Taxcode"    ),
                #("FLAnno.igds Subdivision", "TaxlotsFD/SubdivisionAnno",   "TaxlotsFD/Subdivision"),
                ("FLAnno.igds TaxlotAcres", "TaxlotsFD/TaxlotAcresAnno",   "TaxlotsFD/Taxlot"     ),
           ]
    
    for (layername, outputname, linkedname) in linklist:
        
        annolayer = arcpy.mapping.ListLayers(mxd, layername, df)[0]

# per conversation with Dean on 1/22/18, dont do feature linked annotation.
        
        linkedfc = None
#        if linkedname: 
#            linkedfc = os.path.join(destination, linkedname)
#            if not arcpy.Exists(linkedfc):
#                aprint("ERROR: skipping \"%s\", because linked fc \"%s\" does not exist." % (layername,linkedname))
#                continue
    
        outputfc  = os.path.join(destination, outputname)

        if overwrite or (not arcpy.Exists(outputfc)):
            if overwrite:
                try:
                    deletefc(outputfc)
                except Exception as e:
                    # Probably a schema lock on one feature class, log and press on.
                    msg = "convert_anno: %s" % e
                    logging.error(msg)
                    eprint(msg)
                    warning += 1
                    continue
            success = import_anno(annolayer, outputfc, linkedfc, reference_scale)
            if not success: warning += 1
            
        if arcpy.Exists(outputfc) and (int(arcpy.GetCount_management(annolayer).getOutput(0)) > 0):
            fix_fontsize(outputfc)
            fix_caret(outputfc)

    return warning


# ========================================================================
        
if __name__ == "__main__":

    workfolder = "C:\\GeoModel\\Clatsop\\Workfolder"
    target = "t4-10"
    
    sourcedir = os.path.join(workfolder, target)
    geodatabase = os.path.join(sourcedir, "ORMAP-SchemaN_08-21-08.mdb")

    print("Importing features...")
    import_all_features(sourcedir, geodatabase)

    print("Importing annotation...")
    
    # "overwrite" allows skipping existing annotation classes
    # so you can set it to "false" to just do the calc field steps (which is fast)
    
    overwrite = False
    overwrite = True

    mxdname = os.path.join(workfolder, target, "Annotation.mxd")
    output_workspace = geodatabase
    mxd = arcpy.mapping.MapDocument(mxdname)
    reference_scale = "1200"
    convert_anno(mxd, output_workspace, reference_scale, overwrite)
    del mxd # release schema locks

    print("Tests completed.")

# That's all!
