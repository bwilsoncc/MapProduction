# -*- coding: utf-8 -*-
"""
Created on Tue Dec 19 15:43:00 2017

@author: bwilson
"""
from __future__ import print_function
import arcpy
import os, sys
from zoomToMapNumber import update_page_layout

def print_map(mxdname, map_number, output_type, output_file):
    """Set up a page and print it. """
    
    print("MXD name:", mxdname)
    print("Output type:", output_type)
    print("Output file:", output_file)

    arcpy.AddMessage("Map number: %s" % map_number)
    update_page_layout(mxdname, map_number)
    
    return

def print_maps(mxdname, map_numbers, output_type, output_file):
    """Set up each page and print it. """
    
    l_map_numbers = map_numbers.split(';')
    for map_number in l_map_numbers:
        print_map(mxdname, map_number, output_type, output_file)
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
        map_numbers = "8.10.8BB"#;8.10.25;8.10.25*"
        output_file = os.path.join(os.environ["TEMP"],"output.jpg")
        output_type = "JPEG"
    print_maps(mxdname, map_numbers, output_type, output_file)

# That's all
