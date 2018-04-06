# -*- coding: utf-8 -*-
"""
Convert annotation coverages to geodatabase annotation feature classes
@author: Brian Wilson <bwilson@co.clatsop.or.us>
"""
from __future__ import print_function
import arcpy
from arcpy import mapping as MAP
import os, logging
import re
from ormap.arc_utilities import ListFieldNames, DeleteFC
from collections import defaultdict

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

def __fix_fontsize(outputfc):
    logging.info("fix_fontsize(%s)" % outputfc)
    arcpy.CalculateField_management(outputfc, "FontSize", "!MAPSIZE!", "PYTHON", "")
    return

def __fix_caret(fc):
    """ Change carets to degree character in label fields in an annotation featureclass. """
    logging.info("fix_caret(%s)" % fc)
    fields = ListFieldNames(fc)
    if "TextString" in fields:
        arcpy.CalculateField_management(fc, "TextString", "!TextString!.replace('^',u'\xb0')", "PYTHON", "")
    return True

def fix_anno(fc):
    """ Fix the annotation feature class. 
    Make all the carets into "degree" symbols.
    Make all the font sizes something reasonable."""

    if arcpy.Exists(fc):
    
        badfields = [ "TEXT", "LEVEL", "MAPSIZE" ] # these generate errors: "SYMBOL", "ID", "IGDS_", "IGDS_ID" ]
        for f in badfields:
            try:
                arcpy.DeleteField_management(fc, f)
            except Exception as e:
                print(e)
        if int(arcpy.GetCount_management(fc).getOutput(0)):
            __fix_caret(fc)

    return

# Read all the details
# http://desktop.arcgis.com/en/arcmap/latest/tools/conversion-toolbox/import-coverage-annotation.htm

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
        logging.error("merge_anno(%s, %s), \"%s\"" % (srclist, dst, e))
        success = False

    return success
    
def convert_anno(annolayer, outputfc):
    """ Convert a single coverage annotation to feature class annotation. 
    Output feature class is in a geodatabase.
    """
    logging.info("convert_anno(%s, %s)" % (annolayer.name, outputfc))

    # IGNORE SELECTIONS! Otherwise I end up with annotation feature classes with one row...
    arcpy.SelectLayerByAttribute_management(annolayer, "CLEAR_SELECTION")
    annolayer.visible = True

    annocount = 0
    try:
        fc = annolayer.dataSource
        annocount = int(arcpy.GetCount_management(fc).getOutput(0))
    except Exception as e:
        logging.error("convert_anno, exception while counting features: %s" % e)

    if annocount <= 0:
        logging.info("convert_anno: EMPTY %s" % annolayer.name)
    else:    
        # In the recent past I apparently decided I do not need this step?
        #template = os.path.join(destination, "AnnotationFD\\AnnoTEMPLATE")
        #if templated and not arcpy.Exists(dstfc):
        #    arcpy.FeatureClassToFeatureClass_conversion(template, destination, outputname)
        if arcpy.Exists(outputfc):
            arcpy.Delete_management(outputfc)
        try:
            logging.info("Importing coverage anno to gdb.")

            # I tried creating empty template anno fc's but when I used AppendAnnotation_management,
            # it created a whole new set of annotation classes in the append operation
            # instead of using the ones already in the template so 
            # I tore that code out.

            arcpy.ImportCoverageAnnotation_conversion(annolayer, outputfc, 1200.0, "CLASSES_FROM_LEVELS")
            
            #arcpy.AppendAnnotation_management(tmpfc, outputfc, 1200, create_single_class="CREATE_CLASSES")
            #logging.info("Deleting tmp fc.")
            #arcpy.Delete_management(tmpfc)
        except Exception as e:
            logging.error("convert_anno, exception in conversion: %s" % e)
    return

def import_anno(mxdname, geodatabase):
    """ Import annotation coverages into annotation feature classes. """

    workspace = os.path.join(geodatabase, "annotation_fd")

#    infc = os.path.join(workspace, all_taxlot_anno)
#    whereclause = "TextString='99-99' OR TextString='ROAD' OR TextString='WATER' OR TextString='RAIL' OR TextString LIKE 'GAP%'"
#    dropfeatures(infc, whereclause)
#    return

    layers = [
        ("tmpbearingan", "bearing_anno"),
        ("tmpseemapan",  "seemap_anno"),
        ("tmptaxlotan",  "taxlot_anno"),
        ("tmptaxcodan",  "taxcode_anno"),
        ("tmptaxmapan",  "taxmap_anno"),
        ]
    logging.info("import_anno(%s, %s)" % (mxdname, geodatabase))
    mxd = MAP.MapDocument(mxdname)
    df  = MAP.ListDataFrames(mxd)[0]

    for (layername, fc) in layers:
        annolayer = MAP.ListLayers(mxd, layername, df)[0]
        outputfc = os.path.join(workspace, fc)
        convert_anno(annolayer, outputfc)
        fix_anno(outputfc)
        pass
    del mxd # Release schema locks, hopefully.

    return

# ========================================================================

if __name__ == "__main__":

    MYNAME  = os.path.splitext(os.path.split(__file__)[1])[0]
    LOGFILE = MYNAME + ".log"
    FORMAT = '%(asctime)s %(message)s'
    logging.basicConfig(filename=LOGFILE, level=logging.DEBUG, format=FORMAT)
    workspace   = "C:/GeoModel/Clatsop/Workfolder" 
    geodatabase = os.path.join(workspace,"ORMAP_Clatsop.gdb")
    mxdname = os.path.join(workspace, "Annotation.MXD")
    print("Writing log to %s" % LOGFILE)
    import_anno(mxdname, geodatabase)

    print("Tests completed.")

# That's all!

