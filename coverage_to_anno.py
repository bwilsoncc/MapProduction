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
import re
from Toolbox.arc_utilities import aprint, eprint, ListFieldNames, DeleteFC

# ========================================================================

# Use this to fix AnnotationClassId field
# remember to import re

def fixannoclass(currentclassid, level, m):
    """ this code is used as an ArcMap "Field Calculator" since we can't run it from a script. """
    if currentclassid >= 0 and currentclassid <= 3:
        # current classid is acceptable
        return currentclassid
    if level >= 0 and level <= 3:
        # level is acceptable too
        return level
    # we have to cook something reasonable up from mapnumber
    mapnum = m.strip()
    classid = 3               #       1"=2000'
    if mapnum:
        # we have a mapnumber but current classid is unmutual so pick a new one
        mo = re.search(r'(\d)\.(\d+)\.?(\d*)([a-d]?)([a-d]?)', mapnum, flags=re.IGNORECASE)
        try:
            if mo.group(5):
                classid = 0    # QQ   1"=100'
            elif mo.group(4):
                classid = 1    #  Q   1"=200'
            elif mo.group(3):
                classid = 2    #  S   1"=400'
        except Exception as e:
            print(e)
            pass
    return classid

def check_annoscale(fc):
    fields = ["AnnotationClassID", "MAPNUMBER", "level"]
    count = 0
    # Can't use an Insert or UpdateCursor on an annotation featureclass
    with arcpy.da.SearchCursor(fc, fields) as cursor:
        for row in cursor:
            mapnum  = row[1]
            level   = row[2]
            classid = fixannoclass(row[0], level, mapnum)
            if classid == row[2]: 
                count += 1
                continue
            print("%d : %10s %2d %2d" % (row[0], row[1], row[2], classid))
    print(count)
    pass

def fix_fontsize(outputfc):
    logging.info("fix_fontsize(%s)" % outputfc)
    arcpy.CalculateField_management(outputfc, "FontSize", "!MAPSIZE!", "PYTHON", "")
    return

def fix_caret(outputfc):
    logging.info("fix_caret(%s)" % outputfc)
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
  
    logging.info("import_anno(\"%s\", \"%s\")" % (annolayer.name, outputfc)) 
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

def merge_anno(srclist, dst):
    """Merge annotation from srclist to dst fc.
    'srclist' can be either one fc or a list.
    NB Can't use coverage annotation as a source, has to be a fc in the same database as dest.
    """
    success = True
    reference_scale = 1200.0
    try: 
        logging.info("merge_anno(%s, %s)" % (srclist, dst))
        arcpy.AppendAnnotation_management(srclist, dst, reference_scale, 
                                         "CREATE_CLASSES", 
                                         "NO_SYMBOL_REQUIRED", 
                                         "AUTO_CREATE", "AUTO_UPDATE")
        # I should delete the source fc's here, right? Otherwise we end up with about 100 extra fc's.
        if isinstance(srclist,list):
            for s in srclist:
                arcpy.Delete_management(s)
        else:
            arcpy.Delete_management(srclist)

    except Exception as e:
        msg = "merge_anno(%s, %s), \"%s\"" % (srclist, dst, e)
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

    layers = [
        ("TaxmapAnno0100.igds",             "AnnotationFD\\Anno0100Scale",  True),
        ("TaxmapAnno0200.igds",             "AnnotationFD\\Anno0200Scale",  True),
        ("TaxmapAnno0400.igds",             "AnnotationFD\\Anno0400Scale",  True),
        ("TaxmapAnno2000.igds",             "AnnotationFD\\Anno2000Scale",  True),

        ("TaxLotAn.igds",                   "TaxlotsFD\\TaxlotAnno",        False),
        ("TaxCodAn.igds",                   "TaxlotsFD\\TaxCodeAnno",       False),
        ]

#    oldlayers = [   # (    Layer name,              output featureclass,      templated)
#                ("StdAnno.igds 10 scale",   "AnnotationFD\\Anno0010scale",  True),
#                ("StdAnno.igds 20 scale",   "AnnotationFD\\Anno0020scale",  True),
#                ("StdAnno.igds 30 scale",   "AnnotationFD\\Anno0030scale",  True),
#                ("StdAnno.igds 40 scale",   "AnnotationFD\\Anno0040scale",  True),
#                ("StdAnno.igds 50 scale",   "AnnotationFD\\Anno0050scale",  True),
#                ("StdAnno.igds 100 scale",  "AnnotationFD\\Anno0100scale",  True),
#                ("StdAnno.igds 200 scale",  "AnnotationFD\\Anno0200scale",  True),
#                ("StdAnno.igds 400 scale",  "AnnotationFD\\Anno0400scale",  True),
#                ("StdAnno.igds 800 scale",  "AnnotationFD\\Anno0800scale",  True),
#                ("StdAnno.igds 2000 scale", "AnnotationFD\\Anno2000scale",  True),
#    
#                ("FLAnno.igds Taxlot",      "TaxlotsFD\\TaxlotAnno",        False),
#                ("FLAnno.igds Taxcode",     "TaxlotsFD\\TaxCodeAnno",       False),
#                ("FLAnno.igds TaxlotAcres", "TaxlotsFD\\TaxlotAcresAnno",   False),
#               ]
    
    mergelist = []

    for (layername, outputname, templated) in layers:

        try:
            annocoverage = arcpy.mapping.ListLayers(mxd, layername, df)[0]
        except Exception as e:
            aprint("convert_anno: %s" % e)
            warning += 1
            continue

        logging.info("convert_anno: %s => %s" % (layername,outputname))

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
            logging.info("convert_anno: EMPTY %s" % annocoverage)
            warning += 1
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

def __import_anno(workfolder, target):
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

        
if __name__ == "__main__":

    workfolder = "C:\\GeoModel\\Clatsop\\Workfolder"
    target = "t8-9"
    
    gdb = "ORMAP_Clatsop.gdb"
    fc = os.path.join(workfolder, gdb, "TaxlotsFD\\TaxCodeAnno")
    check_annoscale(fc)

    #__import_anno(workfolder, target)
    
    print("Tests completed.")

# That's all!

