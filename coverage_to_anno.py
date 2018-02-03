# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------------
# convert_to_anno.py
# Created on: 2018-02-02 16:29:52.00000
# Description:
# Convert annotation coverages to geodatabase annotation feature classes
# ---------------------------------------------------------------------------
from __future__ import print_function
import arcpy
import os, logging
from Toolbox.arc_utilities import aprint, eprint, ListFieldNames, DeleteFC

# ========================================================================

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

def fix_anno(fc):
    """ Fix the annotation feature class. 
    Make all the carets into "degree" symbols.
    Make all the font sizes something reasonable."""

    if arcpy.Exists(fc) and int(arcpy.GetCount_management(fc).getOutput(0)):
        fix_fontsize(fc)
        fix_caret(fc)

    return

# Read all the details
# http://desktop.arcgis.com/en/arcmap/latest/tools/conversion-toolbox/import-coverage-annotation.htm

def import_anno(annolayer, outputfc, linkedfc):
    success = True 
  
    aprint("Importing \"%s\" to \"%s\" Linked FC: \"%s\"" % (annolayer.name, outputfc, linkedfc)) 
    reference_scale = 1200.0
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
        msg = "import_anno(%s, %s, %s), \"%s\"" % (annolayer, outputfc, linkedfc, e)
        aprint(msg)
        logging.error(msg)
        success = False
        
    return success

def merge_anno(src,dst):
    """Merge annotation from src to dst fc.
    'src' can be either one fc or a list.
    NB Can't use coverage annotation as a source, has to be a fc in the same database as dest.
    """
    success = True
    reference_scale = 1200.0
    try: 
        arcpy.AppendAnnotation_management(src, dst, reference_scale, 
                                         "CREATE_CLASSES", 
                                         "NO_SYMBOL_REQUIRED", 
                                         "AUTO_CREATE", "AUTO_UPDATE")
    except Exception as e:
        msg = "merge_anno(%s, %s), \"%s\"" % (src, dst, e)
        aprint(msg)
        logging.error(msg)
        success = False

    return success
    
def convert_anno(mxd, destination,  target, d_anno):
    """ Convert coverage annotation to feature class annotation. 
    Add new feature class pathnames to a dictionary.
    Return count of warning messages. 
    
    Destination is a geodatabase.

    Builds a dictionary of lists for each fc that can be used to merge them into a single output fc.
    """
        
    warning = 0
    
    # Assumption is that there is only one dataframe in the annotation mxd.
    df = arcpy.mapping.ListDataFrames(mxd)[0]

    layers = [   # (Layer name, output featureclass, templated)
                ("StdAnno.igds 10 scale",   "AnnotationFD\\Anno0010scale",  True),
                ("StdAnno.igds 20 scale",   "AnnotationFD\\Anno0020scale",  True),
                ("StdAnno.igds 30 scale",   "AnnotationFD\\Anno0030scale",  True),
                ("StdAnno.igds 40 scale",   "AnnotationFD\\Anno0040scale",  True),
                ("StdAnno.igds 50 scale",   "AnnotationFD\\Anno0050scale",  True),
                ("StdAnno.igds 100 scale",  "AnnotationFD\\Anno0100scale",  True),
                ("StdAnno.igds 200 scale",  "AnnotationFD\\Anno0200scale",  True),
                ("StdAnno.igds 400 scale",  "AnnotationFD\\Anno0400scale",  True),
                ("StdAnno.igds 800 scale",  "AnnotationFD\\Anno0800scale",  True),
                ("StdAnno.igds 2000 scale", "AnnotationFD\\Anno2000scale",  True),
    
                ("FLAnno.igds Taxlot",      "TaxlotsFD\\TaxlotAnno",        False),
                ("FLAnno.igds Taxcode",     "TaxlotsFD\\TaxCodeAnno",       False),
                ("FLAnno.igds TaxlotAcres", "TaxlotsFD\\TaxlotAcresAnno",   False),
               ]
    
    mergelist = []

    for (layername, outputname, templated) in layers:

        annocoverage = arcpy.mapping.ListLayers(mxd, layername, df)[0]

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
    
        annocount = int(arcpy.GetCount_management(annocoverage).getOutput(0))
        if annocount <= 0:
            continue

        dstfc =  os.path.join(destination, outputname)

        template = os.path.join(destination, "AnnotationFD\\AnnoTEMPLATE")
        if templated and not arcpy.Exists(dstfc):
            arcpy.FeatureClassToFeatureClass_conversion(template, destination, outputname)

        # copy into a tmp space then merge
        tmpfc  = dstfc + "_" + target
        DeleteFC(tmpfc)

        success = import_anno(annocoverage, tmpfc, linkedfc)
        if success:
            d_anno[dstfc].append(tmpfc)
        else:
            warning += 1
            
    if len(mergelist):
        merge_anno(mergelist,dstfc)
        #for tmpfc in mergelist: DeleteFC(tmpfc) # I leave the tmp fc around to help debug

    return warning

# ========================================================================
        
if __name__ == "__main__":

    workfolder = "C:\\GeoModel\\Clatsop\\Workfolder"
    target = "t8-9"
    
    print("Importing annotation...")
    
    # "merge" means add annotation to existing fc
    # in test mode we just want to start over every time
    merge = False

    mxdname = os.path.join(workfolder, target, "Annotation.mxd")
    output_workspace = geodatabase
    mxd = arcpy.mapping.MapDocument(mxdname)
    d_anno = {}
    convert_anno(mxd, output_workspace, d_anno, merge)
    del mxd # release schema locks

    for outputfc in d_anno:
        fix_caret(outputfc)
        fix_fontsize(outputfc)

    print("Tests completed.")

# That's all!

