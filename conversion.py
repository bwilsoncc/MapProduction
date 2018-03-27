# -*- coding: utf-8 -*-
"""
Convert and combine data for all townships.
@author: Brian Wilson <bwilson@co.clatsop.or.us>
"""
from __future__ import print_function
import os, sys, subprocess, logging
from threading import Thread
from time import sleep
from glob import glob
from shutil import copyfile, copytree, rmtree
from collections import defaultdict

import arcpy
from arcpy import mapping as MAP

from update_acres import update_acres
from coverage_to_geodatabase import import_all_features, fix_mapscales, fix_mapacres, fix_linetypes, make_polygons, update_mapindex
from coverage_to_anno import import_anno
from preprocess import preprocess, merge_annotation

MYNAME  = os.path.splitext(os.path.split(__file__)[1])[0]
LOGFILE = MYNAME + ".log"

# =============================================================================

def backup_coverages(srcfolder, dst):
    """ Copy coverage data from the server to a local folder. """
    sourcepath, township = os.path.split(srcfolder)
    dstfolder = os.path.join(dst, township)
    if os.path.exists(dstfolder):
        msg = "Did not copy %s to %s; folder exists." % (township, dst)        
    else:
        copytree(srcfolder, dstfolder)
        msg = "Copied %s from %s to %s" % (township, sourcepath, dst)
    logging.info(msg)
    return

def copy_geodatabase(source, geodatabase):
    (f,e) = os.path.splitext(source)
    if e.lower() == ".gdb":
        copytree(source,geodatabase)
    else:
        copyfile(source, geodatabase)
    logging.info("Copied empty geodatabase to %s" % geodatabase)
        

# =============================================================================
if __name__ == "__main__":

    FORMAT = '%(asctime)s %(message)s'
    logging.basicConfig(filename=LOGFILE, level=logging.DEBUG, format=FORMAT)

    archive            = "x:\\Applications\\GIS\\taxmaped\\Clatsop\\towned"
    #archive           = "c:\\taxmaped_BACKUPS\towned"
    workspace          = "C:\\GeoModel\\Clatsop"
    geodatabase_source = "C:\\GeoModel\\MapProduction\\ORMAP_Clatsop_Schema.gdb"
    geodatabase        = "ORMAP_Clatsop.gdb"

    # Build a list of townships to be processed

    saved = os.getcwd()
    os.chdir(archive)
    # Convert the entire county
    townships = glob("t[4-9]-*")
    # ORMAP grant project area
    townships = ["t6-6","t6-7","t7-6","t7-7","t8-6","t8-7","t9-6","t9-7"]
    # Uncomment to select one township for testing
    #townships = ["t8-7"]
    # ...or one row of townships to include testing merging
    #townships = glob("t4-*")
    # ...or with an empty list, you can test the code outside the "for" loop...
    #townships = []
    os.chdir(saved)

    sourcefolder = os.path.join(workspace, "Source")
    homefolder   = os.path.join(workspace, "Workfolder")
    gdb          = os.path.join(homefolder, geodatabase) # Combined workspace

    print("Writing log to %s." % LOGFILE)
    logging.info("----------- CONVERSION STARTING -------------")
    ok = True

    # Make a backup copy of the cartographer's files then use the backup as the source for our work.
    # This step is totally unnecessary but it should speed up testing since the data will be on the local drive.
    # If you really want the copy to happen you must delete the Source/ folder contents
    # since this function will not overwrite.
    for township in townships:
        backup_coverages(os.path.join(archive, township), sourcefolder)

    if os.path.exists(gdb):
        logging.info("Merging data into existing \"%s\"." % gdb)
    else:       
        # Create a blank geodatabase from the template.
        copy_geodatabase(geodatabase_source, gdb)

    for township in townships:
        logging.info("Processing %s" % township)

        sourcefullpath    = os.path.join(sourcefolder, township) 
        workfolder        = os.path.join(workspace, "Workfolder", township)

        if os.path.exists(workfolder): 
            print("Delete %s if you want to re-import it." % township)

        amlsource = os.path.join(workspace, "AML")
        ok = preprocess(amlsource, sourcefullpath, workfolder)     
        if not ok: 
            logging.warn("Preprocessing completed with errors.")

        import_all_features(workfolder, gdb)

    logging.info("Convert annotation for %s" % township)
    merge_annotation(townships, homefolder) # Make one big coverage for each annotation group
    
    # Before you get here, use Arcmap to adjust settings in the MXD to control font color and size...
    mxdname = os.path.join(homefolder, "Annotation.mxd")
    if not os.path.exists(mxdname):
        logging.error("MXD \"%s\" not found." % mxdname)
    else:
        import_anno(mxdname, gdb)
        pass

    saved = arcpy.env.workspace
    arcpy.env.workspace = os.path.join(gdb, "taxlots_fd")

    make_polygons("mapindex_lines", "mapindex_points", "mapindex")
    make_polygons("taxcode_lines",  "taxcode_points",  "taxcode")
    make_polygons("taxlot_lines",   "taxlot_points",   "taxlot")

    update_mapindex("mapindex")

    fix_mapscales(["mapindex"])
    fix_mapacres("taxlot")
    fix_linetypes(["taxlot"])

    arcpy.env.workspace = saved

    if ok: 
        print("All done!")
    else:
        print("We finished with errors!")
    logging.info("Conversion completed.")

# That's all!
