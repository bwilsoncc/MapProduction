# -*- coding: utf-8 -*-
"""
Created on Tue Dec 19 15:43:00 2017

@author: bwilson
"""
from __future__ import print_function
import arcpy
from arcpy import mapping as MAP

def update_page_layout(mxdname, map_number):
    """Update the current map document (CURRENT) page layout using the given map_number."""
    
    print(mxdname)
    print(map_number)
    mxd = MAP.MapDocument(mxdname)
    print("MXD name = ", mxdname)
    print("MXD file = ", mxd.filePath)
    return

# ======================================================================

# UNIT TESTING
# You can run this file directly when writing it to aid in debugging

if __name__ == '__main__':
    
    mxdname = "MapIndex.mxd"
    map_number = "8.10.8BB"
    update_page_layout(mxdname, map_number)
    
# That's all
