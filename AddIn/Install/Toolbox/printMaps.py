# -*- coding: utf-8 -*-
"""
Created on Tue Dec 19 15:43:00 2017

@author: bwilson
"""
from __future__ import print_function
import arcpy
import time
from zoomToMapNumber import update_page_layout

def print_a_map(mxdname, map_number, output_type, output_file):
    """Set up a page and print it. """
    
    print("MXD name:", mxdname)
    print("Map number:", map_number)
    print("Output type:", output_type)
    print("Output file:", output_file)

    update_page_layout(mxdname, map_number)
    
    for t in range(0,10):
        arcpy.AddMessage("Working.. %d" % t)
        time.sleep(1)
    
    return

# ======================================================================

# UNIT TESTING
# You can run this file directly when writing it to aid in debugging

if __name__ == '__main__':
    
    mxdname = "MapIndex.mxd"
    map_number = ""
    output_type = "JPEG"
    output_file = "output.jpg"
    
    print_a_map(mxdname, map_number, output_type, output_file)
# That's all
