# -*- coding: utf-8 -*-
"""
Set up all townships for conversion.

@author: bwilson
"""
from __future__ import print_function
import os
from glob import glob
from shutil import copyfile, copytree, rmtree
import sys, subprocess
import arcpy

from coverage_to_geodatabase import import_all


# =============================================================================

def copy_coverages(workspace):
    # Copy coverages from the file server to a local folder
    source = os.path.join(sourcedir,tfolder)
    dest   = os.path.join(workspace,"Source",tfolder)
    print("%s  =>  %s" % (source,dest))
    rmtree(dest, ignore_errors = True)
    copytree(source, dest)

def run_aml(aml, datafolder, workfolder):    
    """ Run an AML file; but before running it, 
        put the correct strings into the AMLs to describe source and output locations.""" 

    # We have to store the patched AML files somewhere
    # before running them.
    temp = os.environ['TEMP']

    amlfolder, amlbase = os.path.split(aml)
    amlname, amlext = os.path.splitext(amlbase)
    
    with open(aml,"r") as fp:
        lines = fp.readlines()

    # Clear out the remnants of any previous conversion.
    workfolder = os.path.join(workspace, "Workfolder")
    rmtree(workfolder, ignore_errors = True)
    os.mkdir(workfolder)

    # Stash the AML files somewhere and run "arc" from this folder
    # so we don't need a complicated &run command.

    cwd = os.getcwd()    
    os.chdir(temp)
    
    # Copy the source of this AML file,
    # while hacking the correct folder paths into it,
    # and forcing the log file to a more sensible setting.
    
    with open(amlbase,"w") as fp:
        for line in lines:
            line = line.replace("${WORKFOLDER}", workfolder)
            line = line.replace("${SOURCEFOLDER}", datafolder)
            if line.find("&WATCH")>=0:
                logfile = os.path.join(workfolder, amlname + '.log')
                line = "&WATCH " + logfile + "\n"
            fp.write(line)
    
    args = ["c:/arcgis/arcexe9x/bin/arc", "&r " + amlbase]
    
    # Run our AML
    print(amlbase)
    p = subprocess.check_output(args)
    print("AML %s said:" % amlbase)
    print(p)
    
    os.chdir(cwd)
    return

def copy_geodatabase(source, geodatabase):
    if os.path.exists(geodatabase): return
    copyfile(source, geodatabase)
    print("Copied empty geodatabase to %s" % geodatabase)
        
def copy_mxds(sourcedir, workspace):
    for s,d in [("ConversionTEMPLATE.mxd","Conversion.mxd"),("AnnoTemplate.mxd","AnnoTemplate.mxd")]:
        source = os.path.join(sourcedir, s)
        dest   = os.path.join(workspace, d)
        copyfile(source, dest)
        #repair_mxd(dest)
        
def repair_mxd(mxdname):
    # I changed the MXD so this should not be necessary 
    # Data sources will still point at the source folder.
    print("%s repaired." % mxdname)
    m = arcpy.mapping.MapDocument(mxdname)
    newpath = os.path.join()
    m.findAndReplaceWorkspacePaths(oldpath,newpath,validate=True)
    pass
                
def make_folders(workspace):    

    for d in [workspace,
              os.path.join(workspace, "ConvertII"),
           ]:
        if not os.path.exists(d): 
            os.mkdir(d)
            print("%s created." % d)
        
            
# =============================================================================
if __name__ == "__main__":

    datasource = "k:\\taxmaped\\Clatsop\\towned"
    sourcedir = "C:\\GeoModel\\Clatsop"
    outputdir  = sourcedir
    geodatabase = "ORMAP-SchemaN_08-21-08.mdb"

    os.chdir(datasource)
    sources = [ tfolder for tfolder in glob("t[0-9]-*") ]
    
    for source in sources:
        target = "T%sN%sW" % (source[1], source[3:])
        print("Working on", target)
        
        workspace = os.path.join(outputdir, target)
        make_folders(workspace)
        
        # Copy a blank geodatabase into our workspace.
        # (Skipped if the geodabase already exists.)
        sourcegdb = os.path.join(sourcedir, "ORMAP-SchemaN_08-21-08", geodatabase)
        gdb       = os.path.join(workspace, geodatabase)
        copy_geodatabase(sourcegdb, gdb)
        
        original_coverages = os.path.join(datasource, source)
        
        coverage_folder = os.path.join(workspace, "Source")
        preprocess_folder = os.path.join(workspace, "Workfolder")
        
        # Copy the original coverages into the workspace "Source" folder
        if not os.path.exists(coverage_folder): 
            copytree(original_coverages, coverage_folder)
            print("Copied original coverage data to %s" % coverage_folder)

        # Step 3. Run the preprocess amls to prepare for geodatabase import
        
        for aml in glob(os.path.join(sourcedir, "ConvertAmls", "[0-9][0-9]-*.aml")):
            run_aml(aml, coverage_folder, preprocess_folder)

        # This will replace any previously imported feature classes;
        # it does a "delete all" followed by an append.
        import_all(preprocess_folder, gdb)

        # Copy the supporting MXD's into our workspace
        copy_mxds(sourcedir, workspace)
        #import_annotation(preprocess_folder, gdb)
        
    print("All done!")
# That's all!
