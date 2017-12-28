# -*- coding: utf-8 -*-
"""
Created on Tue Dec 19 15:43:00 2017

@author: bwilson
"""
from __future__ import print_function
import arcpy
from arcpy import mapping as MAP
import os, sys
from zoomToMapNumber import update_page_layout
from time import sleep

def print_map(mxd, map_number, output_type, output_file):
    """Set up a page and print it. """
    
    msg = "Adjusting layout for %s" % map_number
    arcpy.SetProgressorLabel(msg)
        
    update_page_layout(mxd, map_number)
    
    if os.path.exists(output_file):
        os.unlink(output_file)

    msg = "Exporting to %s" % output_file
    arcpy.SetProgressorLabel(msg)

    if output_type == 'PDF':
        MAP.ExportToPDF(mxd, output_file)
    elif output_type == 'JPEG':
        MAP.ExportToJPEG(mxd, output_file)
    else:
        print("Here is where we'd actually send the map to a printer.")
        
    return

def print_maps(mxd, map_numbers, output_type, output_pathname):
    """Set up each page and print it. """

    output_path = "C:\\TempPath"
    output_file = "output"

    if output_type == "PDF":
        output_ext = ".pdf"
    elif output_type == "JPEG":
        output_ext = ".jpg"
    else:
        output_ext = ".prn"
        
    arcpy.AddMessage("output_pathname = %s" % output_pathname)
    (output_path, output_fileext) = os.path.split(output_pathname)
    (output_file, output_ext)     = os.path.splitext(output_fileext)

    l_map_numbers = map_numbers.split(';')

    start    = 0
    maxcount = len(l_map_numbers)
    step     = 1
    
    if maxcount>1:
        arcpy.SetProgressor("step", "Printing %d maps." % maxcount, start, maxcount, step)
    else:
        arcpy.SetProgressor("default", "Printing %s" % l_map_numbers[0])
        
    print("Output type:", output_type)
    t = 0
    for map_number in l_map_numbers:

        map_name = map_number.replace('*','').replace('%','') # remove wildcards

        pathname = os.path.join(output_path, output_file + '_' + map_name + output_ext)
        print("Output file:", pathname)
        print("Map number: %s" % map_number)
        print_map(mxd, map_number, output_type, pathname)

        t += 1
        arcpy.SetProgressorPosition(t)
    sleep(2) # Give ArcMap a chance to catch up with us.

    return

# ======================================================================

# UNIT TESTING
# You can run this file directly when writing it to aid in debugging

if __name__ == '__main__':
    try:
        # Try to run as a python script (from ArcMap)
        mxdname = "CURRENT"
        map_numbers = sys.argv[1]
        output_type = sys.argv[2]
        output_file = sys.argv[3]
    except IndexError:
        # No go, run from debugger (perhaps)
        mxdname = "TestMap.mxd"
        map_numbers = "8.10.8BB;8.10.25*"
        output_file = os.path.join(os.environ["TEMP"],"output.jpg")
        output_type = "JPEG"
    mxd = MAP.MapDocument(mxdname)
    print_maps(mxd, map_numbers, output_type, output_file)
    del mxd
# That's all
