# -*- coding: utf-8 -*-
"""
Set up all townships for conversion.

@author: bwilson
"""
from __future__ import print_function
import os, sys, subprocess, logging
from threading import Thread
from Queue import Queue, Empty
from time import sleep
from glob import glob
from shutil import copyfile, copytree, rmtree
import arcpy
from arcpy import mapping as MAP
from Toolbox.arc_utilities import aprint, eprint
from update_acres import update_acres
from coverage_to_geodatabase import import_all_features, convert_anno

LOGFILE = "conversion.log"

ON_POSIX = 'posix' in sys.builtin_module_names
q = Queue()

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
    
        Use full paths for everything; arc finds relative paths confusing. This is because
        the &WORKSPACE command does a CHDIR and therefore Arc forgets what the current folder is.
        Anyway. Use full paths for all parameters.
        
        "amlsource" is the path to a file containing AML code
        "coverage_folder" is the location of the source coverage data
        "preprocess_folder" is location where the coverages will be written
        
        AML files and WATCH files will be written into the preprocess_folder
    """ 

    verbose = False # Show all output of AML scripts.

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

    print(amltmp)
    
    # Start "arc" running as a child process and grab its stdout.
    p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize=1, close_fds=ON_POSIX)

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
                if countdown < 10: print(countdown)
                sleep(1)
                countdown -= 1
        else:
            countdown = restart # Keep going
            if verbose: print(line.strip())
            if line.find("AML MESSAGE")>=0:
                if line.find("Stopping execution")>=0:
                    msg = "%s:Stopping execution on %s" % (amltmp, preprocess_folder)
                    logging.warning(msg)
                    print(msg)
                    countdown = 10 # give it another 10 seconds
                else:
                    logging.warning(amltmp + ":" + line.strip())
                    if not verbose: print(line.strip())
            elif line.find("DO YOU WANT TO TRY AGAIN?")>=0:
                logging.warning(amltmp + ":" + line.strip())
                msg = "%s:INPUT PROMPT. %s" % (amltmp, preprocess_folder)
                logging.warning(msg)
                print(msg)
                countdown = 5 # give it another second
                
    if retcode == None:
        # Still running
        msg = "Terminating process %d and its children." % p.pid
        logging.error(amltmp + ":" + msg)
        print(msg)
        # Can't do simple terminate because "arc" starts subprocesses like "arcedit".
        # /T option causes child processes to be taken down too.
        # /F means "force".
        subprocess.call(['taskkill', '/F', '/T', '/PID', str(p.pid)])
        ok = False

    return ok

def copy_coverages(datasource, source, coverage_folder):
    """ Copy the original coverages into our workspace "Source" folder. 
        Will not overwrite coverage_folder. """
    original_coverages = os.path.join(datasource, source)
    if not os.path.exists(coverage_folder): 
        copytree(original_coverages, coverage_folder)
        aprint("Copied original coverage data to %s" % coverage_folder)
    return

def preprocess(amlsource_folder, preprocess_folder, coverage_folder):
    """ Step 3. Run the preprocess amls to prepare for geodatabase import. 
    Run all AML scripts, and return False if any of them failed to complete. """

    rval = True # Assume all is well in the world
    
    # Clear out the remnants of any previous conversion
    rmtree(preprocess_folder, ignore_errors=True)
    if not os.path.exists(preprocess_folder): os.mkdir(preprocess_folder)
    os.chdir(preprocess_folder)

    # We run 01-14 because #15 is BROKEN -- read the docs!
            
    for amlnumber in range(1,15):
        amlfile = glob(os.path.join(amlsource_folder, "%02d-*.aml" % amlnumber))[0]
        #print(amlfile, coverage_folder, preprocess_folder)
        ok = run_aml(amlfile, coverage_folder, preprocess_folder)
        if not ok: rval = False 
    
    count = update_acres(os.path.join("taxacan", "annotation.igds"))
    logging.info("TAXACRES updated in %d rows" % count)

    return rval

def copy_geodatabase(source, geodatabase):
    copyfile(source, geodatabase)
    print("Copied empty geodatabase to %s" % geodatabase)
        
def repair_layer(lyr, oldp, newp):
    # Show ONLY layers with a query.
    #if not(lyr.supports("DEFINITIONQUERY") and lyr.definitionQuery): return

    rcount = 0
        
    if lyr.supports("DATASOURCE"):

        ds = os.path.normcase(lyr.dataSource)
        op = os.path.normcase(oldp)
        #np = os.path.normcase(newp)        
        #print("          %s" % lyr.dataSource)
        #print("    old   %s" % oldp)
        #print("    new?  %s" % newp)
        if ds.find(op)==0:
            #print("   Layer: %s" % lyr.longName)
            dataset = ds[len(op)+1:]
            if dataset.find(".mdb")>0:
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
        
def repair_mxd(mxdname, sourcedir, workfolder, target):
    
    #print("----------------------------------------")
    #print(mxdname)
    m = arcpy.mapping.MapDocument(mxdname) 
    mdb = "ORMAP-SchemaN_08-21-08.mdb"
    count = 0
    l_df = MAP.ListDataFrames(m)
    for df in l_df:
        for lyr in MAP.ListLayers(m, "", df):
            oldpath = os.path.join(sourcedir, mdb)
            newpath = os.path.join(workfolder, target, mdb)
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
            
def install_mxds(sourcedir, workfolder, target):
    for s,d in [
                ("ConversionTEMPLATE.mxd","Conversion.mxd"),
                ("AnnoTEMPLATE.mxd","Annotation.mxd")
                ]:
        source = os.path.join(sourcedir, s)
        dest   = os.path.join(workfolder, target, d)
        if not os.path.exists(dest):
            print(source, " ==>", dest)
            copyfile(source, dest)
            repair_mxd(dest, sourcedir, workfolder, target)

# =============================================================================
if __name__ == "__main__":

    logging.basicConfig(filename=LOGFILE,level=logging.DEBUG)

    #datasource  = "k:\\taxmaped\\Clatsop\\towned"
    datasource  = "c:\\taxmaped_BACKUPS"
    sourcedir   = "C:\\GeoModel\\Clatsop"
    workspace   = sourcedir
    geodatabase = "ORMAP-SchemaN_08-21-08.mdb"

    # Do everything  
    sources = [ tfolder for tfolder in glob(os.path.join(datasource,"t[4-9]-*"))]
    
    # Uncomment to select one township for testing
    sources = [ tfolder for tfolder in glob(os.path.join(datasource,"t4-10"))]

    # If this is set to True then existing "preprocess" coverages will be removed and rebuilt
    overwrite = True
    overwrite = False
    
    overwrite_anno = True        
    overwrite_anno = False
    
    ok = True

    for sourcefullpath in sources:
        sourcepath, source = os.path.split(sourcefullpath)

        preprocess_folder  = os.path.join(workspace, "Workfolder", source)

        msg = "Preprocessing %s" % source
        do_preprocess = True
        if os.path.exists(preprocess_folder):
            if overwrite:
                msg = "Overwriting %s" % source
            else:
                msg = "Skipping preprocessing on %s; folder exists." % source
                do_preprocess = False
        
        logging.info(msg)
        aprint(msg)
        saved = os.getcwd()
        
        if do_preprocess:

            coverage_folder = os.path.join(workspace, "Source", source)
            copy_coverages(datasource, source, coverage_folder)

            
            amlsource = os.path.join(sourcedir, "ConvertAmls")
            ok = preprocess(amlsource, preprocess_folder, coverage_folder)     
            if not ok: 
                logging.warn("Preprocessing completed with errors.")
    
        # Copy a blank geodatabase into our workspace.
        sourcegdb = os.path.join(sourcedir, "ORMAP-SchemaN_08-21-08", geodatabase)
        gdb       = os.path.join(preprocess_folder, geodatabase)
        if os.path.exists(gdb):
            msg = "Skipping geodatabase conversion; ORMAP gdb exists."
            logging.info(msg)
            aprint(msg)
        else:       
            copy_geodatabase(sourcegdb, gdb)
            # This will replace any previously imported feature classes;
            # it does a "delete all" followed by an append.
            import_all_features(preprocess_folder, gdb)

        # Copy the supporting MXD's into our workspace
        install_mxds(sourcedir, os.path.join(workspace, "Workfolder"), source)
        
        logging.info("Convert annotation %s" % source)
        reference_scale = "1200"
        mxdname = os.path.join(preprocess_folder, "Annotation.mxd")
        mxd = MAP.MapDocument(mxdname)
        convert_anno(mxd, gdb, reference_scale, overwrite_anno)
        del mxd # release schema locks
        
        os.chdir(saved)

    if ok: 
        print("All done!")
    else:
        print("We finished with errors!")
# That's all!
