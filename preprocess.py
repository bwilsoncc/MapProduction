# -*- coding: utf-8 -*-
"""
Run the AML code that does the preprocessing steps.
This modifies the coverages so that they are ready to be imported into the geodatabase.
(It creates a copy of each coverage and then modifies the copy.)

This corresponds to "Step 3" in my notes.

@author: Brian Wilson <bwilson@co.clatsop.or.us>
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
from Toolbox.ormapnum import ormapnum

MYNAME  = os.path.splitext(os.path.split(__file__)[1])[0]
LOGFILE = MYNAME + ".log"

ON_POSIX = 'posix' in sys.builtin_module_names
q = Queue()

verbose = True

# =============================================================================

def enqueue_output(out, q):
    # Read STDOUT lines from the running copy of arc
    for line in iter(out.readline, b''):
        # Got a line, put it into the FIFO QUEUE
        q.put(line)
    out.close()
    return

def run_aml(amlsource, sourcefolder):    
    """
    Run an AML file
    
    Use full paths for everything; arc finds relative paths confusing. Be aware
    the &WORKSPACE command does a CHDIR anyway.
        
    "amlsource" is the path to a file containing AML code
    "source_folder" is the location of the source coverage data
        
    AML files and WATCH files will be written into the workspace (cwd)
    """ 
    args = ["c:/arcgis/arcexe9x/bin/arc", "&r " + amlsource, sourcefolder]
    
    ok = True
    
    # Start "arc" running as a child process and grab its stdout.

    p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize=1, close_fds=ON_POSIX)

    # Create a thread and connect the output from "arc" to it
    t = Thread(target=enqueue_output, args=(p.stdout,q))
    t.daemon = True
    t.start()

    # Wait for input from the child
    # Look for error messages
    # If it's been a long time, kill the child process. (Sad!)
    
    restart   = 120 # yes it can take this long sometimes!
    countdown = restart # Wait for a response
    retcode   = None
    while (countdown>0):
        try:
            line = q.get_nowait()
        except Empty:
            retcode = p.poll()
            if retcode != None:
                logging.debug("Arc returned : %s" % retcode)
                countdown=0
            else:
                if countdown < 10: print(countdown)
                sleep(1)
                countdown -= 1
        else:
            countdown = restart # Keep going
            #if verbose: print(line.strip())
            if line.find("AML MESSAGE")>=0:
                if line.find("Stopping execution")>=0:
                    msg = "%s:Stopping execution on %s" % (amlsource, sourcefolder)
                    logging.warning(msg)
                    print(msg)
                    countdown = 10 # give it another 10 seconds
                else:
                    logging.warning(amlsource + ":" + line.strip())
                    if not verbose: print(line.strip())
            elif line.find("DO YOU WANT TO TRY AGAIN?")>=0:
                logging.warning(amlsource + ":" + line.strip())
                msg = "%s:INPUT PROMPT. %s" % (amlsource, sourcefolder)
                logging.warning(msg)
                print(msg)
                countdown = 5 # give it another second
                
    if retcode == None:
        # Still running
        msg = "Terminating process %d and its children." % p.pid
        logging.error(amlsource + ":" + msg)
        # Can't do simple terminate because "arc" starts subprocesses like "arcedit".
        # /T option causes child processes to be taken down too.
        # /F means "force".
        subprocess.call(['taskkill', '/F', '/T', '/PID', str(p.pid)])
        ok = False

    return ok

def posttaxmap(workfolder):
    """ Code to run after stage 01.
    Fix taxbound ormapnum, the AML code to create ormapnum is broken for detail maps. """

    fc = os.path.join(workfolder, "tmptaxmap1/point")
    #fc = os.path.join(workfolder, "taxbound/label")

    logging.info("post01(%s)" % fc)

    fields = ["ORMAPNUM", "PAGENAME", "MAPSUFNUM", "OID@"]
    ORMAPNUM  = 0
    PAGENAME  = 1
    MAPSUFNUM = 2
    OID       = 3

    orm = ormapnum()
    
    with arcpy.da.UpdateCursor(fc, fields) as cursor:
        for row in cursor:
            o   = row[ORMAPNUM]
            oid = row[OID]
            if not o:
                try:
                    # mysteriously, some ormapnumbers are just empty
                    cursor.deleteRow()
                    logging.debug("Deleted empty row.")
                except Exception as e:
                    logging.warn("Could not delete empty row(%s). %s" % (oid, e))
                continue

        # repair detail map number
            if o[-1] == 'D':
                o += "%03d" % row[MAPSUFNUM]
                orm.unpack(o)
                row[ORMAPNUM] = orm.ormapnumber 
                logging.info("Repaired %s" % row[ORMAPNUM])

            try:
                orm.unpack(o)
            except ValueError as e:
                logging.warn(e)

            if orm.township == 0 or orm.range == 0:
                try:
                    # mysteriously, some ormapnumbers are 0,0
                    cursor.deleteRow()
                    logging.debug("Deleted 0,0 row.")
                except Exception as e:
                    logging.warn("Could not delete 0,0 row(%s). %s" % (oid, e))
                continue

        # calc page number from ormapnum
            row[PAGENAME] = orm.shorten()
            cursor.updateRow(row)
            pass
    return

def preprocess(codefolder, sourcefolder, workfolder):
    ok = True
    l_aml = [
        "01-tmptaxmap1",

        "02-mapindex",
        "02-taxbound",
        "02-taxcode",
        "02-taxlot",

        "04-tmptaxmap2",
        
        "05-annotation",        

        # These are all basically the same code, but I am not up to refactoring them today.
        # They can execute in any order as long as it's after tmptaxmap2 and taxbound get built
        "06-cornerpoints",
        "06-cartolines",
        "06-plsslines",
        "06-reflines",
        "06-waterlines",

        ]
    saved = os.getcwd()

    for aml in l_aml:
        pyfun = None
        if type(aml) is tuple:
            pyfun = aml[1]
            aml = aml[0]

        # Clear out the remnants of any previous conversion
        # I do this manually
        #rmtree(workfolder, ignore_errors=True)

        if not os.path.exists(workfolder): 
            os.mkdir(workfolder)

        os.chdir(workfolder) # This is the AML workspace

        # Use the existence of a WAT file as evidence we don't need to rerun a step
        wat = aml + ".wat"
        if not os.path.exists(wat):
            logging.info(aml)
            if not run_aml(os.path.join(codefolder, aml), sourcefolder):
                ok = False
            elif pyfun:
                pyfun(workfolder)

        else:
            logging.info("Skipping %s because .WAT exists." % (aml))
        pass # end of "for"

    os.chdir(saved)
    
#    count = update_acres(os.path.join("taxacan", "annotation.igds"))
#    logging.info("TAXACRES updated in %d rows" % count)

    return ok
        
# =============================================================================
if __name__ == "__main__":

    MYNAME  = os.path.splitext(os.path.split(__file__)[1])[0]
    LOGFILE = MYNAME + ".log"
    FORMAT = '%(asctime)s %(message)s'
    logging.basicConfig(filename=LOGFILE, level=logging.DEBUG, format=FORMAT)

    workspace = "C:\\GeoModel\\Clatsop"
    source_folder = os.path.join(workspace, "Source")

    # Do everything  
    #sources = [ tfolder for tfolder in glob(os.path.join(source_folder,"t[4-9]-*"))]
    # Uncomment to select one township for testing
    sources = [ tfolder for tfolder in glob(os.path.join(source_folder, "t6-10"))]
    # ...or one row of townships
    #sources = [ tfolder for tfolder in glob(os.path.join(source_folder,"t4-[67]*"))]
    # ...or with an empty list, you can test the code outside the "for" loop...
    #sources = []

    logging.info("preprocess(%s)" % sources)
    ok = True

    for sourcefullpath in sources:
        sourcepath, township = os.path.split(sourcefullpath)
        workfolder = os.path.join(workspace, "Workfolder", township)

        msg = "Preprocessing township %s" % township
        logging.info(msg)
           
        amlsource = os.path.join(workspace, "AML")
        ok = preprocess(amlsource, sourcefullpath, workfolder)     
        if not ok: 
            logging.warning("Preprocessing completed with errors.")

    if ok: 
        print("All done!")
    else:
        print("We finished with errors!")

# That's all!
