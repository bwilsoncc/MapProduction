# -*- coding: utf-8 -*-
"""
Convert and combine data for all townships.

@author: bwilson
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

from Toolbox.mxdrepair import install_mxds
from update_acres import update_acres
from coverage_to_geodatabase import import_all_features, fix_mapscales, make_polygons, update_mapindex
from coverage_to_anno import convert_anno, merge_anno, fix_anno
from preprocess import preprocess

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

    archive            = "k:\\taxmaped\\Clatsop\\towned"
    #archive           = "c:\\taxmaped_BACKUPS\towned"
    workspace          = "C:\\GeoModel\\Clatsop"
    geodatabase_source = "C:\\GeoModel\\MapProduction\\ORMAP_Clatsop_Schema.gdb"
    geodatabase        = "ORMAP_Clatsop.gdb"

    # Convert the entire county, this is the normal default  
    archives = [ tfolder for tfolder in glob(os.path.join(archive,"t[4-9]-*"))]
    # Uncomment to select one township for testing
    #archives = [ tfolder for tfolder in glob(os.path.join(archive,"t6-10"))]
    # ...or one row of townships to include testing merging
    #archives = [ tfolder for tfolder in glob(os.path.join(archive,"t4-*"))]
    # ...or with an empty list, you can test the code outside the "for" loop...
    #archives = []

    ok = True
    sourcefolder = os.path.join(workspace, "Source")
    homefolder   = os.path.join(workspace, "Workfolder")
    merged_gdb   = os.path.join(homefolder, geodatabase) # Combined workspace
    d_anno = defaultdict(list)

    # Make a backup copy of the cartographer's files then use the backup as the source for our work.
    # This step is totally unnecessary but it should speed up testing since the data will be on the local drive.
    # If you really want the copy to happen you must delete the Source/ folder contents
    # since this function will not overwrite.
    for archivefullpath in archives:
        backup_coverages(archivefullpath, sourcefolder)

    if os.path.exists(merged_gdb):
        logging.info("Merging data into existing \"%s\"." % merged_gdb)
    else:       
        # Create a blank geodatabase from the template.
        copy_geodatabase(geodatabase_source, merged_gdb)

    for archivefullpath in archives:
        archive, township = os.path.split(archivefullpath)
        sourcefullpath    = os.path.join(sourcefolder, township) 
        workfolder        = os.path.join(workspace, "Workfolder", township)

#        if os.path.exists(workfolder): 
#            print("Delete %s if you want to re-process it." % workfolder)
#            continue

        logging.info("Processing %s" % township)

        amlsource = os.path.join(workspace, "AML")
        ok = preprocess(amlsource, sourcefullpath, workfolder)     
        if not ok: 
            logging.warn("Preprocessing completed with errors.")

        # UNFORTUNATELY
        # there is no way to merge from coverage annotation into annotation feature class, only IMPORT
        # so on the first pass I import annotation into a separate feature class
        # then append into the combined.
        # BUT WAIT, there's more! "Append" only works if the feature classes are in the same database!
        # So I can't build a scratch database for each township and then merge them!

        # If I could then output could go to this township gdb.
        # Use this code if you don't want all the data in one geodatabase at the end.
        unmerged_gdb = os.path.join(sourcefullpath, geodatabase) # Worksace per township
        #if not os.path.exists(unmerged_gdb):
        #    # Create a blank geodatabase from the template.
        #    copy_geodatabase(geodatabase_source, unmerged_gdb)

        import_all_features(workfolder, merged_gdb, merge=True)

        # Copy the supporting MXD's into our workspace
        # This also "repairs" data sources if they need to be
        install_mxds(workspace, homefolder, geodatabase, township)
        
        logging.info("Convert annotation for %s" % township)
        mxdname = os.path.join(workfolder, "Annotation.mxd")
        if not os.path.exists(mxdname):
            logging.error("MXD \"%s\" not found." % mxdname)
        else:
            mxd = MAP.MapDocument(mxdname)
            convert_anno(mxd, merged_gdb, township.replace('-','_'), d_anno)
            del mxd # release schema locks

    for dst in d_anno:
        merge_anno(d_anno[dst], dst)
        
        # I don't think you can run this here, because it's trying to run on 
        # an annotation feature class, so this is not supported by arcpy.
        # You'd have to run it manually as a field calc operation in ArcMap
        # fix_anno(dst)

        pass

    saved = arcpy.env.workspace
    arcpy.env.workspace = os.path.join(merged_gdb, "TaxlotsFD")
    make_polygons("TaxcodeLines", "TaxcodePoints", "Taxcode")
    make_polygons("TaxlotLines", "TaxlotPoints", "Taxlot")
    make_polygons("MapIndexLines", "MapIndexPoints", "MapIndex")
    update_mapindex(os.path.join(arcpy.env.workspace, "MapIndex")) # why don't they use workspace?
    arcpy.env.workspace = saved

    fix_mapscales(merged_gdb, ["MapIndex"])

    if ok: 
        print("All done!")
    else:
        print("We finished with errors!")

# That's all!
