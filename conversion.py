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

schema    = "ORMAP-SchemaN_08-21-08.mdb"

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
    print("dry run ", amlbase)
    #p = subprocess.check_output(args)
    #print("AML %s said:" % amlbase)
    #print(p)
    
    os.chdir(cwd)
    return

def copy_schema(source, workspace):
    dest = os.path.join(workspace, schema)
    if os.path.exists(dest): return
    
    source = os.path.join(source, "ORMAP-SchemaN_08-21-08", schema)
    copyfile(source, dest)
    print("Copied schema to %s" % workspace)
        
def copy_mxds(sourcedir, workspace):
    for tool in ["Conversion.mxd","AnnoTemplate.mxd"]:
        source = os.path.join(sourcedir, tool)
        dest   = os.path.join(workspace, tool)
        copyfile(source, dest)
        repair_mxd(dest)
        
def repair_mxd(mxdname):
    # Data sources will still point at the source folder.
    print("%s repaired." % mxdname)
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
    
    os.chdir(datasource)
    sources = [ tfolder for tfolder in glob("t[0-9]-*") ]
    
    for source in sources:
        target = "T%sN%sW" % (source[1], source[3:])
        print("Working on", target)
        
        workspace = os.path.join(outputdir, target)
        make_folders(workspace)
        copy_schema(sourcedir, workspace)
        copy_mxds(sourcedir, workspace)

        coverage_source = os.path.join(datasource, source)
        coverage_folder = os.path.join(workspace, "Source")
        output_folder = os.path.join(workspace, "Workfolder")
        if not os.path.exists(coverage_folder): 
            copytree(coverage_source, coverage_folder)
            print("Copied original coverage data to %s" % coverage_folder)

        for aml in glob(os.path.join(sourcedir, "ConvertAmls", "[0-9][0-9]-*.aml")):
            run_aml(aml, coverage_folder, output_folder)

    print("All done!")
# That's all!
