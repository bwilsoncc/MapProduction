# -*- coding: utf-8 -*-
"""
Set up all townships for conversion.

@author: bwilson
"""
from __future__ import print_function
import os, sys, subprocess
from threading import Thread
from Queue import Queue, Empty
from time import sleep
from glob import glob
from shutil import copyfile, copytree, rmtree
import arcpy
from Toolbox.arc_utilities import aprint, eprint
from coverage_to_geodatabase import import_all

ON_POSIX = 'posix' in sys.builtin_module_names
q = Queue()
verbose = False # Show all output of AML scripts.

# =============================================================================

def enqueue_output(out, q):
    # Read STDOUT lines from the running copy of arc
    for line in iter(out.readline, b''):
        # Got a line, put it into the FIFO QUEUE
        q.put(line)
    out.close()
    return

def run_aml(amlsource, coverage_folder, preprocess_folder):    
    """ Run an AML file; but before running it, 
        put the correct strings into the AMLs to describe source and output locations.
    
        Use full paths for everything. Arc finds relative paths confusing.
        The &WORKSPACE command does a CHDIR and therefore Arc forgets what the current folder is.
        I think this is what happens when ESRI has talented high school students write their code.
        Anyway. Use full paths for all parameters.
        
        amlsource is the path to a file containing AML code
        coverage_folder is the location of the source coverage data
        preprocess_folder is location where the coverages will be written
        
        AML files and WATCH files will be written into the preprocess_folder
    """ 

    with open(amlsource,"r") as fp:
        lines = fp.readlines()

    amlfolder, amlbase = os.path.split(amlsource)
    amlname, amlext = os.path.splitext(amlbase)

    # Copy the source of this AML file to CWD,
    # while hacking the correct folder paths into it,
    # and forcing the log file to a more sensible setting.
        
    edit = False # Run the original, unmodified scripts in ConvertAmls
    edit = True  # Copy and edit the scripts to point at this township's folders.
    startcomment =  "/* --- start\n"
    endcomment   =  "/* --- end\n"
    if edit: 
        amltmp = amlbase
        with open(amltmp,"w") as fp:
            logfile = amlname + '.wat'
            line = startcomment 
            line += "&WORKSPACE %s\n" % preprocess_folder
            line += "&WATCH %s &COMMANDS\n" % logfile 
            line += "&s source = %s\n" % coverage_folder
        
            line += endcomment
            fp.write(line)
            droplines = False
            for line in lines:
                if line.find(startcomment)>=0:
                    droplines = True
                    continue
                elif line.find(endcomment)>=0:
                    droplines = False
                    continue
                if not droplines:
                    fp.write(line)
    else:
        amltmp = amlsource
        
    args = ["c:/arcgis/arcexe9x/bin/arc", "&r " + amltmp]
    
    # Run our AML
    ok = True
    aprint("Running %s" % amltmp)

    # Start "arc" running as a child process and grab its stdout.
    p = subprocess.Popen(args, stdout=subprocess.PIPE, bufsize=1, close_fds=ON_POSIX)

    # Create a thread and connect the output from "arc" to it
    t = Thread(target=enqueue_output, args=(p.stdout,q))
    t.daemon = True
    t.start()

    # Wait for input from the child
    # Look for error messages
    # If it's been a long time, kill the child process (so so sad)
    
    restart   = 30
    countdown = restart # Wait up to 5 seconds for a response
    retcode   = None
    while (countdown>0):
        try:
            line = q.get_nowait()
        except Empty:
            retcode = p.poll()
            if retcode != None:
                #print("Return code from Arc was", retcode)
                countdown=0
            else:
                if countdown < 5: print(countdown)
                sleep(.5)
                countdown -= 1
        else:
            countdown = restart # Keep going
            if verbose: print(line.strip())
            if line.find("AML MESSAGE")>=0:
                if not verbose: print(line.strip())
                if line.find("Stopping execution")>=0:
                    print("Stopping execution of %s on %s" % (amltmp, preprocess_folder))
                    countdown = 2 # stop soonish
                
    if retcode == None:
        # Still running
        print("Terminating process %d and its children." % p.pid)
        # Can't do simple terminate because "arc" starts subprocesses like "arcedit".
        # /T option causes child processes to be taken down too.
        # /F means "force".
        subprocess.call(['taskkill', '/F', '/T', '/PID', str(p.pid)])
        ok = False

    return ok

def copy_geodatabase(source, geodatabase):
    if os.path.exists(geodatabase): return
    #copyfile(source, geodatabase)
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
            
# =============================================================================
if __name__ == "__main__":

    #datasource  = "k:\\taxmaped\\Clatsop\\towned"
    datasource  = "c:\\taxmaped_BACKUPS"
    sourcedir   = "C:\\GeoModel\\Clatsop"
    workspace   = sourcedir
    geodatabase = "ORMAP-SchemaN_08-21-08.mdb"

    # Do everything  
    sources = [ tfolder for tfolder in glob(os.path.join(datasource,"t[4-9]-*"))]
    
    # Uncomment to select one township for testing
    sources = [ tfolder for tfolder in glob(os.path.join(datasource,"t4-10"))]

    # If this is set to True then existing coverages will be removed and rebuilt
    overwrite = True
    
    ok = True

    for sourcefullpath in sources:
        sourcepath, source = os.path.split(sourcefullpath)
        target = "T%sN%sW" % (source[1], source[3:])

        preprocess_folder  = os.path.join(workspace, "Workfolder", source)

        # Dont overwrite, press forward
        if os.path.exists(preprocess_folder):
            if overwrite:
                aprint("Overwriting %s" % source)
            else:
                aprint("Skipping %s" % source)
                continue
        else:
            aprint("Creating %s" % source)
        
        # Copy a blank geodatabase into our workspace.
        # (Skipped if the geodabase already exists.)
        sourcegdb = os.path.join(sourcedir, "ORMAP-SchemaN_08-21-08", geodatabase)
        gdb       = os.path.join(workspace, geodatabase)
        copy_geodatabase(sourcegdb, gdb)
        
        # Copy the original coverages into the workspace "Source" folder

        original_coverages = os.path.join(datasource, source)
        coverage_folder    = os.path.join(workspace, "Source", source)
               
        if not os.path.exists(coverage_folder): 
            copytree(original_coverages, coverage_folder)
            aprint("Copied original coverage data to %s" % coverage_folder)

        # Step 3. Run the preprocess amls to prepare for geodatabase import

        saved = os.getcwd()

        # Clear out the remnants of any previous conversion
        rmtree(preprocess_folder, ignore_errors=True)
        if not os.path.exists(preprocess_folder): os.mkdir(preprocess_folder)
        os.chdir(preprocess_folder)

        # We run 01-14 because #15 is BROKEN -- read the docs!
        
        for amlnumber in range(1,15):
            amlfile = glob(os.path.join(sourcedir, "ConvertAmls", "%02d-*.aml" % amlnumber))[0]
            #print(amlfile, coverage_folder, preprocess_folder)
            ok = run_aml(amlfile, coverage_folder, preprocess_folder)
            if not ok: 
                print("Pressing on after catching an error.")
            pass
        #if not ok: break
    
        # This will replace any previously imported feature classes;
        # it does a "delete all" followed by an append.
        #import_all(preprocess_folder, gdb)

        # Copy the supporting MXD's into our workspace
        #copy_mxds(sourcedir, workspace)
        #import_annotation(preprocess_folder, gdb)
        
        os.chdir(saved)

    if ok: 
        print("All done!")
    else:
        print("We finished with errors!") 
# That's all!
