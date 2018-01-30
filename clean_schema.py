# -*- coding: utf-8 -*-
"""
Remove all the leftover data from a schema file.

Deletes the features from feature classes;
excludes any feature class with name starting with "MapIndex".

Created on Tue Jan 30 09:09:15 2018

@author: Brian Wilson <bwilson@co.clatsop.or.us>
"""
from __future__ import print_function
import os, sys
import arcpy

# =============================================================================
def delfeat(fc):
    """ Snatching victory from the hands of delfeat. """
    
    # The neutron bomb approach, delete all the data
    # but leave the buildings standing.
    arcpy.DeleteFeatures_management(fc)
    pass
    
def clean(gdb):
    arcpy.env.workspace = gdb
    fds = arcpy.ListDatasets()
    for fd in fds:
        print(fd)
        arcpy.env.workspace = os.path.join(gdb,fd)
        fcs = arcpy.ListFeatureClasses()
        for fc in fcs:
            if fc.find("MapIndex")>=0: 
                continue
            d = arcpy.Describe(fc)
            print("  %s/%s %s" % (fd,fc, d.featureType))
            #delfeat(fc)
            pass
        
    arcpy.env.workspace = gdb
    fcs = arcpy.ListFeatureClasses()
    for fc in fcs:
        d = arcpy.Describe(fc)
        print(fc, d.featureType)
        if fc.find("MapIndex")>=0: 
            continue
        #delfeat(fc)
        pass
    
# =============================================================================
if __name__ == "__main__":
    clean("C:\\GeoModel\\MapProduction\\ORMAP_Clatsop_Schema.gdb")
    print("That's all!")
    
# That's all!

