# -*- coding: utf-8 -*-
"""
Created on Tue Dec 19 15:43:00 2017

@author: bwilson
"""
from __future__ import print_function
import arcpy
from arcpy import mapping as MAP
import os, sys
from ormap.arc_utilities import aprint, eprint
from zoomToMapNumber import update_page_layout
from time import sleep

def print_map(mxd, pagename, output_type, output_file):
    """Set up a page and print it. """
            
    arcpy.SetProgressorLabel("Exporting to %s" % output_file)

    update_page_layout(mxd, pagename)
    
    if os.path.exists(output_file):
        os.unlink(output_file)

    msg = ""
    if output_type == 'PDF':
        try:
            MAP.ExportToPDF(mxd, output_file)
            msg = "Completed %s" % output_file
        except Exception as e:
            msg = "Export to PDF failed with '%s'." % e
            pass
    else:
        try:
            MAP.ExportToJPEG(mxd, output_file)
            msg = "Completed %s" % output_file
        except Exception as e:
            msg = "Export to JPEG failed with '%s'." % e
            pass
    aprint(msg)
    return

def print_maps(mxd, pagenames, output_type, output_pathname):
    """Set up each page and print it. """

    if output_type == "PDF":
        output_ext = ".pdf"
    else:
        output_ext = ".jpg"
        
    #arcpy.AddMessage("output_pathname = %s" % output_pathname)
    (output_path, output_fileext) = os.path.split(output_pathname)
    (output_file, output_ext)     = os.path.splitext(output_fileext)

    l_pagenames = pagenames.split(';')

    start    = 0
    maxcount = len(l_pagenames)
    step     = 1
    
    if len(l_pagenames) <= 0:
        eprint("No map numbers found to print.")
        return

    if maxcount>1:
        arcpy.SetProgressor("step", "Printing %d maps." % maxcount, start, maxcount, step)
    else:
        arcpy.SetProgressor("default", "Printing %s" % l_pagenames[0])
        
    t = 0
    # ESRI likes to wrap parameters strings in quotes, for some unknown reason.
    for mn in l_pagenames:
        pagename = mn.strip("\"'")
        filename = output_file + pagename.replace(' ', '_')
        pathname = os.path.join(output_path, filename + output_ext)
        #print("Output file:", pathname)
        print_map(mxd, pagename, output_type, pathname)

        t += 1
        arcpy.SetProgressorPosition(t)
        sleep(3) # Give ArcMap a chance to catch up with us. Superstition.

    if t>1: arcpy.SetProgressorLabel("Completed %d maps." % t)
    return

# ======================================================================

# UNIT TESTING
# You can run this file directly when writing it to aid in debugging

if __name__ == '__main__':
    try:
        # Try to run as a python script (from ArcMap)
        mxdname = "CURRENT"
        pagenames = sys.argv[1]
        output_type = sys.argv[2]
        output_file = sys.argv[3]
    except IndexError:
        # No go, run from debugger (perhaps)
        mxdname = "C:\\GeoModel\\Clatsop\\Workfolder\TestMap.mxd"
        pagenames = "8 10 8BB;8 10 25"
        output_file = os.path.join(os.environ["TEMP"],"printmap-unittest-.jpg")
        output_type = "JPEG"
    mxd = MAP.MapDocument(mxdname)
    print_maps(mxd, pagenames, output_type, output_file)
    del mxd
    print("Tests completed.")
# That's all
