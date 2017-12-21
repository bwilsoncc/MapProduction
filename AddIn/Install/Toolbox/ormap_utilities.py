# -*- coding: utf-8 -*-
"""
Created on Wed Dec 20 10:41:09 2017

A collection of utilities to help with the map production toolbox.

@author: bwilson
"""
from __future__ import print_function
import os, sys
import arcpy
from arcpy import mapping as MAP

# =============================================================================
# Load the "configuration files"
# NB, force string into lower case to make sure it works in Windows
configpath = os.path.dirname(__file__)
if not configpath: configpath = os.getcwd()
configpath=configpath.replace("Toolbox","Config")
print("__file__", __file__, "configpath", configpath)
sys.path.append(configpath)

import ORMAP_LayersConfig as ORMapLayers
import ORMAP_MapConfig as ORMapPageLayout
print(ORMapLayers.__file__, ORMapPageLayout.__file__)

def aprint(msg):
    """ Print a message. Execution does not stop. """
    print(msg)
    sys.stdout.flush()
    arcpy.AddMessage(msg)

def eprint(msg):
    """ Print a message. Execution will stop when you use this one. """
    print("ERROR:",msg)
    arcpy.AddError(msg)

def get_dataframe(mxd, dfname):
    """ Return the named dataframe object. """
    df = None
    try:
        df = MAP.ListDataFrames(mxd, dfname)[0]
    except Exception as e:
        aprint("Dataframe not found. Make sure it is named '%s'. \"%s\"" % (dfname,e))
    return df

def get_layer(mxd, df, layername):
    layer = None
    try:
        layer = MAP.ListLayers(mxd, layername, df)[0]
    except Exception as e:
        print("Can't find layer \"%s\". \"%s\"" % (layername, e))
    return layer

def set_definition_query(mxd, df, layername, query):
    """ Set the definition query on a layer. """
    if df:
        layer = get_layer(mxd, df, layername)
        try:
            layer = MAP.ListLayers(mxd, layername, df)[0]
            layer.definitionQuery = query
        except Exception as e:
            print("Can't set query \"%s\" on layer \"%s\". \"%s\"" % (query, layername, e))
            return False
    return True

def list_mapnumbers(fc, mapnum_fieldname):
    d_val = {}
    with arcpy.da.SearchCursor(fc, [mapnum_fieldname]) as cursor:
        for row in cursor:
            if row[0]: d_val[row[0]] = True
    return [mapnum for mapnum in d_val]
        
# =============================================================================
if __name__ == "__main__":
    # unit tests
    
    # In real life this will normally be "CURRENT".
    mxdname = "TestMap.mxd"
    
    dfname = ORMapLayers.MainDF
    layername = ORMapLayers.MAPINDEX_LAYER
    mxd = MAP.MapDocument(mxdname)
    df = get_dataframe(mxd, dfname)
    layer = get_layer(mxd, df, layername)
    print(layer.dataSource)
    l = list_mapnumbers(layer.dataSource, ORMapLayers.MapNumberField)
    print(l)
    del mxd
    
# That's all!

