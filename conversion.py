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

from Toolbox.arc_utilities import aprint, eprint
from update_acres import update_acres
from coverage_to_geodatabase import import_all_features, fix_mapscales, convert_anno, merge_anno, fix_anno
from preprocess import preprocess

MYNAME  = os.path.splitext(os.path.split(__file__)[1])[0]
LOGFILE = MYNAME + ".log"

# =============================================================================

def backup_coverages(srcfolder, dst):
    """ Copy coverage data from the server to a local folder. """
    sourcepath, township = os.path.split(srcfolder)
    dstfolder = os.path.join(dst, township)
    if os.path.exists(dstfolder):
        msg = "Did not copy of %s to %s; folder exists." % (township, dst)        
    else:
        copytree(srcfolder, dstfolder)
        msg = "Copied %s from %s to %s" % (township, sourcepath, dst)
    logging.info(msg)
    aprint(msg)
    return

def copy_geodatabase(source, geodatabase):
    (f,e) = os.path.splitext(source)
    if e.lower() == ".gdb":
        copytree(source,geodatabase)
    else:
        copyfile(source, geodatabase)
    print("Copied empty geodatabase to %s" % geodatabase)
        
def repair_layer(lyr, oldp, newp):
    rcount = 0
    ds = os.path.normcase(lyr.dataSource)
    op = os.path.normcase(oldp).rstrip('\\')
    np = os.path.normcase(newp).rstrip('\\')
    if op == np:
        return rcount

    #print("  datasrc %s" % lyr.dataSource)
    #print("    old   %s" % oldp)
    #print("    new?  %s" % newp)
    if ds.find(op)==0:
        #print("   Layer: %s" % lyr.longName)
        dataset = ds[len(op)+1:]
        if dataset.find(".mdb")>0 or dataset.find(".gdb")>0:
            return 0
        #print("***       %s  %s" % (newp, dataset))
        try:
            lyr.findAndReplaceWorkspacePath(oldp, newp, validate=False)
            #print("   Set to %s" % lyr.dataSource)
            rcount = 1
        except ValueError:
            eprint("repair_layer(%s,%s,%s) Replace failed." % (lyr.longName, oldp, newp))
    #print()
        
    return rcount
        
def repair_mxd(mxdname, sourcedir, workfolder, gdb, target, gdb_target):
    
    #print("----------------------------------------")
    #print(mxdname)
    m = arcpy.mapping.MapDocument(mxdname) 
    count = 0
    l_df = MAP.ListDataFrames(m)
    for df in l_df:
        for lyr in MAP.ListLayers(m, "", df):
            if not lyr.supports("DATASOURCE"):
                continue

            oldpath = os.path.join(sourcedir, gdb)
            newpath = os.path.join(workfolder, gdb_target, gdb)
            r = repair_layer(lyr, oldpath, newpath)
            if r:
                count += r
                continue

            # Just hacking around confusing ESRI path
            # Where this comes from is a mystery
            # "C:\GeoModel\Clatsop\Workfolder\t4-10\Workfolder"            
            oldpath = os.path.join(workfolder, target, "Workfolder")
            newpath = os.path.join(workfolder, target)
            r = repair_layer(lyr, oldpath, newpath)
            if r:
                count += r
                continue

            oldpath = workfolder
            r = repair_layer(lyr, oldpath, newpath)
            if r:
                count += r
                continue

    if count>0:
        print("Repaired %d layers." % count)
        m.save()
    else:
        print("Nothing to repair.")
    print()
    
    del m
    
    pass
            
def install_mxds(sourcedir, workfolder, gdb, target):
    for s,d in [
                ("ConversionTEMPLATE.mxd","Conversion.mxd"),
                ("AnnoTEMPLATE.mxd","Annotation.mxd")
                ]:
        source = os.path.join(sourcedir, s)
        dest   = os.path.join(workfolder, target, d)
        if not os.path.exists(dest):
            #print(source, " ==>", dest)
            copyfile(source, dest)

            gdb_target = "" #merged database
            #gdb_target = target #unmerged
            repair_mxd(dest, sourcedir, workfolder, gdb, target, gdb_target)
    return

# =============================================================================
if __name__ == "__main__":

    FORMAT = '%(asctime)s %(message)s'
    logging.basicConfig(filename=LOGFILE, level=logging.DEBUG, format=FORMAT)

    #archive  = "k:\\taxmaped\\Clatsop\\towned"
    archive  = "c:\\taxmaped_BACKUPS"
    sourcedir   = "C:\\GeoModel\\Clatsop"
    workspace   = sourcedir
    #geodatabase_source = "C:\\GeoModel\\Clatsop\\ORMAP-SchemaN_08-21-08\\ORMAP-SchemaN_08-21-08.mdb"
    #geodatabase  = "ORMAP_Clatsop.mdb"
    geodatabase_source = "C:\\GeoModel\\MapProduction\\ORMAP_Clatsop_Schema.gdb"
    geodatabase  = "ORMAP_Clatsop.gdb"

    # Do everything  
    sources = [ tfolder for tfolder in glob(os.path.join(archive,"t[4-9]-*"))]
    # Uncomment to select one township for testing
    sources = [ tfolder for tfolder in glob(os.path.join(archive,"t8-[89]"))]
    # ...or one row of townships
    #sources = [ tfolder for tfolder in glob(os.path.join(archive,"t4-[67]*"))]
    # ...or with an empty list, you can test the code outside the "for" loop...
    #sources = []

    # If this is set to True then existing "preprocess" coverages will be removed and rebuilt
    overwrite = True
    overwrite = False

    ok = True

    merged_gdb = os.path.join(workspace, "Workfolder", geodatabase) # Combined workspace
    d_anno = defaultdict(list)

    # Make a backup copy of the cartographer's files then use the backup as the source for our work.
    # This step is totally unnecessary but it should speed up testing since the data will be on the local drive.
    # If you really want the copy to happen you must delete the Source/ folder contents
    # since this function will not overwrite.
    for sourcefullpath in sources:
        backup_coverages(sourcefullpath, os.path.join(workspace, "Source"))

    if os.path.exists(merged_gdb):
        msg = "Merging data into existing \"%s\"." % merged_gdb
        logging.info(msg)
        aprint(msg)
    else:       
        # Create a blank geodatabase from the template.
        copy_geodatabase(geodatabase_source, merged_gdb)

    for sourcefullpath in sources:
        continue
        sourcepath, township = os.path.split(sourcefullpath)
              
        amlsource = os.path.join(sourcedir, "ConvertAmls")
        amlsource = os.path.join("C:\\GeoModel\\MapProduction\\Dean\AML")
        ok = preprocess(amlsource, preprocess_folder, coverage_folder)     
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
        unmerged_gdb = os.path.join(preprocess_folder, geodatabase) # Worksace per township
        #if not os.path.exists(unmerged_gdb):
        #    # Create a blank geodatabase from the template.
        #    copy_geodatabase(geodatabase_source, unmerged_gdb)

        #import_all_features(preprocess_folder, merged_gdb, merge=True)

        # Copy the supporting MXD's into our workspace
        # This also "repairs" coverage annotation data sources so that they point at the correct data.

        install_mxds(sourcedir, os.path.join(workspace, "Workfolder"), geodatabase, source)
        
        logging.info("Convert annotation %s" % source)
        mxdname = os.path.join(preprocess_folder, "Annotation.mxd")
        if not os.path.exists(mxdname):
            eprint("MXD \"%s\" not found." % mxdname)
        else:
            mxd = MAP.MapDocument(mxdname)
            convert_anno(mxd, merged_gdb, source.replace('-','_'), d_anno)
            del mxd # release schema locks

    for dst in d_anno:
        #merge_anno(d_anno[dst], dst)
        #fix_anno(dst)
        pass

    #fix_mapscales(merged_gdb)

    if ok: 
        print("All done!")
    else:
        print("We finished with errors!")

# That's all!

