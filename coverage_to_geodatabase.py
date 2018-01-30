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
from Toolbox.arc_utilities import aprint, eprint, ListFieldNames, DeleteFC

# ========================================================================

def import_features(coverage, fc, merge):
    """ Import a coverage into a geodatabase feature class.
    The output feature class has to exist. If "merge" = False,
    then delete any existing features first. """

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
    
    if not merge:
        try:
            arcpy.DeleteFeatures_management(fc)
        except Exception as e:
            logging.error("import_features(%s,%s) DeleteFeatures :%s" % (coverage,fc, e))

    try:
        arcpy.Append_management(coverage, fc, "NO_TEST")
    except Exception as e:
        logging.error("import_features(%s,%s) Append :%s" % (coverage,fc, e))
        
    return True

def import_all_features(source_folder, geodatabase, merge=False):

    # First item is coverage name, second is featureclass name
    table_xlat = [
        ("mapindex\\polygon", "TaxlotsFD\\MapIndex",      "MapScale"),

        ("cartolin\\arc",     "CartographicLines",        "MapScale"),
        ("corner\\point",     "Corner",                   "MapScale"),
        ("plssline\\arc",     "PLSSLines",                "MapScale"),
        ("refline\\arc",      "ReferenceLines",           "MapScale"),
        ("taxcode\\arc",      "TaxlotsFD\\TaxCodeLines",  None),
        ("taxcode\\polygon",  "TaxlotsFD\TaxCode",        None),
        ("taxlot\\arc",       "TaxlotsFD\\TaxlotLines",   None),
        ("taxlot\\polygon",   "TaxlotsFD\\Taxlot",        None),
        ("waterlin\\arc",     "Waterlines",               "MapScale"),
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
        import_features(srccvg, destfc, merge)
            
        arcpy.SetProgressorPosition(t)

    return True

def fix_mapscale(fc):
    """ Fix the values of a mapscale column, if they are not already correct. """

    scales = {
        10:120,
        20:240,
        30:360,
        40:480,
        50:600,
        100:1200,
        200:2400,
        400:4800,
        800:9600,
        1000:12000,
        2000:24000}

    if not arcpy.Exists(fc) or int(arcpy.GetCount_management(fc).getOutput(0)) == 0:
        return
    d = arcpy.Describe(fc)
    if d.featureType != "Simple":
        return
    for f in ListFieldNames(fc):
        if f.lower() == 'mapscale':
            aprint("Recalculating %s in %s." % (f,fc))
            with arcpy.da.UpdateCursor(fc, [f]) as cursor:
                for row in cursor:
                    try:
                        newscale = scales[row[0]]
                        row[0] = newscale
                        cursor.updateRow(row)
                    except KeyError:
                        continue # Probably does not need updating
            break
    return

def fix_mapscales(gdb):
    """ Fix the "mapscale" field in every feature class in a geodatabase. """
    saved = arcpy.env.workspace
    arcpy.env.workspace = gdb

    fdlist = arcpy.ListDatasets()
    if fdlist: 
        for fd in fdlist:
            for fc in arcpy.ListFeatureClasses(feature_dataset=fd):
                fix_mapscale(fc)

    for fc in arcpy.ListFeatureClasses():
        fix_mapscale(fc)

    arcpy.env.workspace = saved
    return

# ---------------------------------------------------------------------------

def fix_fontsize(outputfc):
    aprint("fix_fontsize(%s)" % outputfc)
    arcpy.CalculateField_management(outputfc, "FontSize", "!MAPSIZE!", "PYTHON", "")

def fix_caret(outputfc):
    aprint("fix_caret(%s)" % outputfc)
    fields = ListFieldNames(outputfc)
    if "TEXT_" in fields:
        arcpy.CalculateField_management(outputfc, "TEXT_",      "!TEXT_!.replace('^',u'\xb0')",      "PYTHON", "")
    if "TextString" in fields:
        arcpy.CalculateField_management(outputfc, "TextString", "!TextString!.replace('^',u'\xb0')", "PYTHON", "")
    return True

def fix_anno(gdb):
    """ Fix all the annotation feature classes in a geodatabase. 
    Make all the carets into "degree" symbols.
    Make all the font sizes something reasonable."""

    saved = arcpy.env.workspace
    arcpy.env.workspace = gdb
    fdlist = arcpy.ListDatasets()
    if fdlist: 
        for fd in fdlist:
            for fc in arcpy.ListFeatureClasses(feature_type="Annotation",feature_dataset=fd):
                if arcpy.Exists(fc) and int(arcpy.GetCount_management(fc).getOutput(0)):
                    fix_fontsize(fc)
                    fix_caret(fc)
    fclist = arcpy.ListFeatureClasses(feature_type = "Annotation")
    if fclist:
        for fc in fclist:
            if arcpy.Exists(fc) and int(arcpy.GetCount_management(fc).getOutput(0)):
                fix_fontsize(fc)
                fix_caret(fc)

    arcpy.env.workspace = saved
    return


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
                                                  "CLASSES_FROM_LEVELS",
                                             
                                                  "NO_MATCH", # or maybe you can get "MATCH_FIRST_INPUT" to work, I can't 
                                                  #"MATCH_FIRST_INPUT", # use symbology from first input layer when merging 
                                                  
                                                  "NO_SYMBOL_REQUIRED",
                                                  linked, linkedfc, "AUTO_CREATE", "AUTO_UPDATE")
    except Exception as e:
        msg = "import_anno(%s, %s, %s, %s), \"%s\"" % (annolayer, outputfc, linkedfc, reference_scale, e)
        aprint(msg)
        logging.error(msg)
        success = False
        
    return success

def merge_anno(src,dst):
    """Merge annotation from src fc to dst fc. 
    NB Can't merge coverage annotation
    """
    success = True
    try: 
        arcpy.AppendAnnotation_management(src, dst, 1200.0, 
                                         "CREATE_CLASSES", 
                                         "NO_SYMBOL_REQUIRED", 
                                         "AUTO_CREATE", "AUTO_UPDATE")
    except Exception as e:
        msg = "merge_anno(%s, %s), \"%s\"" % (src, dst, e)
        aprint(msg)
        logging.error(msg)
        success = False

    return success
    
def convert_anno(mxd, destination,  reference_scale, merge=False):
    """ Convert coverage annotation to feature class annotation. 
    Add new feature class pathnames to a dictionary.
    Return count of warning messages. 
    
    Destination is a geodatabase... alas this generated fc has to have a unique name
    because all the anno has to be written to one gdb so that the append function will work!
    """
        
    warning = 0
    
    # Assumption is that there is only one dataframe in the annotation mxd.
    df = arcpy.mapping.ListDataFrames(mxd)[0]

    linklist = [   # (Layer name, output featureclass, reference scale)
                ("StdAnno.igds 10 scale",   "AnnotationFD/Anno0010scale",  None),
                ("StdAnno.igds 20 scale",   "AnnotationFD/Anno0020scale",  None),
                ("StdAnno.igds 30 scale",   "AnnotationFD/Anno0030scale",  None),
                ("StdAnno.igds 40 scale",   "AnnotationFD/Anno0040scale",  None),
                ("StdAnno.igds 50 scale",   "AnnotationFD/Anno0050scale",  None),
                ("StdAnno.igds 100 scale",  "AnnotationFD/Anno0100scale",  None),
                ("StdAnno.igds 200 scale",  "AnnotationFD/Anno0200scale",  None),
                ("StdAnno.igds 400 scale",  "AnnotationFD/Anno0400scale",  None),
                ("StdAnno.igds 800 scale",  "AnnotationFD/Anno0800scale",  None),
                ("StdAnno.igds 2000 scale", "AnnotationFD/Anno2000scale",  None),
                
                # These could be use_level="ONE_CLASS_ONLY"
                ("FLAnno.igds Taxlot",      "TaxlotsFD/TaxlotAnno",        None),
                ("FLAnno.igds Taxcode",     "TaxlotsFD/TaxCodeAnno",       None),
                ("FLAnno.igds TaxlotAcres", "TaxlotsFD/TaxlotAcresAnno",   None),
               ]
    
    for (layername, outputname, refscale) in linklist:
        
        annolayer = arcpy.mapping.ListLayers(mxd, layername, df)[0]

# per conversation with Dean on 1/22/18, dont do feature linked annotation.
# per conversation with Adam 1/26, it's really not needed right now anyway;
# creating a new taxlot is not a daily thing and moving one is very rare
# so maintaining the annotation separately is not onerous.
        
        linkedfc = None
#        if linkedname: 
#            linkedfc = os.path.join(destination, linkedname)
#            if not arcpy.Exists(linkedfc):
#                aprint("ERROR: skipping \"%s\", because linked fc \"%s\" does not exist." % (layername,linkedname))
#                continue
    
        dstfc =  os.path.join(destination, outputname)

        if merge:
            # copy into a tmp pace then merge
            tmpfc  = dstfc + "_tmp"
            DeleteFC(tmpfc)
            pass
        else:
            # not merging so skip the copy/append/delete schtick
            tmpfc = dstfc
            DeleteFC(dstfc)

        if not refscale: refscale = reference_scale
        success = import_anno(annolayer, tmpfc, linkedfc, refscale)
        if success:
            if merge: 
                merge_anno(tmpfc,dstfc)
                DeleteFC(tmpfc)
        else:
            warning += 1
            
    return warning


# ========================================================================
        
if __name__ == "__main__":

    workfolder = "C:\\GeoModel\\Clatsop\\Workfolder"
    target = "t4-10"
    
    sourcedir = os.path.join(workfolder, target)
    geodatabase = os.path.join(workfolder, "ORMAP_Clatsop.gdb")
    fix_mapscales(geodatabase)
    fix_anno(geodatabase)
    exit(0)

    #print("Importing features...")
    d_features = {}
    #import_all_features(sourcedir, geodatabase, d_features)
    for outputfc in d_features:
        fix_mapscale(outputfc, d_features[outputfc])
    print("Importing annotation...")
    
    # "merge" means add annotation to existing fc
    # in test mode we just want to start over every time
    merge = False

    mxdname = os.path.join(workfolder, target, "Annotation.mxd")
    output_workspace = geodatabase
    mxd = arcpy.mapping.MapDocument(mxdname)
    reference_scale = "1200"
    d_anno = {}
    convert_anno(mxd, output_workspace, reference_scale, d_anno, merge)
    del mxd # release schema locks

    for outputfc in d_anno:
        fix_caret(outputfc)
        fix_fontsize(outputfc)

    print("Tests completed.")

# That's all!
