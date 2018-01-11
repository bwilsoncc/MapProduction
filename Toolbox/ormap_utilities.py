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
from arc_utilities import aprint, eprint, get_dataframe, get_layer
from ormapnum import ormapnum
import mapnum

# =============================================================================
# Load the "configuration files"
# NB, force string into lower case to make sure it works in Windows
configpath = os.path.dirname(__file__)
if not configpath: configpath = os.getcwd()
configpath=configpath.replace("Toolbox","Config")
#print("__file__", __file__, "configpath", configpath)
sys.path.append(configpath)

import ORMAP_LayersConfig as ORMapLayers
import ORMAP_MapConfig as ORMapPageLayout
print(ORMapLayers.__file__, ORMapPageLayout.__file__)

def set_definition_query(mxd, df, layername, query):
    """ Set the definition query on a layer. """
    if df:
        layer = get_layer(mxd, df, layername)
        if not layer: return False
        try:
            layer.definitionQuery = query
        except Exception as e:
            print("Can't set query \"%s\" on layer \"%s\"/\"%s\". \"%s\"" % (query, df.name, layername, e))
            return False
    return True

def list_mapnumbers(fc, mapnum_fieldname):
    """Return a sorted list of the contents of the short mapnumber field in a featureclass. 
    The problem with this field is that it does not know about "detail" and "supplemental" maps. """
    d_val = {} # use a dict to get rid of duplicates
    with arcpy.da.SearchCursor(fc, [mapnum_fieldname]) as cursor:
        for row in cursor:
            if row[0]:
                mn = mapnum.mapnum(row[0])
                d_val[mn.number] = row[0]
    return [d_val[k] for k in sorted(d_val)]
 
def list_ormapnumbers(fc, mapnum_fieldname):
    """Return a sorted list of the shortened contents of ormapnumber field in a featureclass. 
    The shortened version is similar to the "mapnum" field but has the map suffix appended if it exists,
    for example "8.10.8.DC D1" indicates detail map #1 """
    d_val = {} # use a dict to get rid of duplicates
    orm = ormapnum()
    with arcpy.da.SearchCursor(fc, [mapnum_fieldname]) as cursor:
        for row in cursor:
            if row[0]:
                orm.unpack(row[0])
                d_val[row[0]] = orm.shorten()

    return [d_val[k] for k in sorted(d_val)]
 
# =============================================================================
if __name__ == "__main__":
    # unit tests
    
    # In real life this will normally be "CURRENT".
    mxdname = "TestMap.mxd"
    
    dfname = ORMapLayers.MainDF
    layername = ORMapLayers.MainLayers[0][0]
    mxd = MAP.MapDocument(mxdname)
    df = get_dataframe(mxd, dfname)
    layer = get_layer(mxd, df, layername)
    
    aprint("layer.dataSource=%s" % layer.dataSource)
    
    aprint("mapnumbers")
    l = list_mapnumbers(layer.dataSource, ORMapLayers.MapNumberField)
    for m in l: aprint(m)

    aprint("ormapnumbers")
    l = list_ormapnumbers(layer.dataSource, ORMapLayers.ORMapNumberField)
    for m in l: aprint(m)

    del mxd
    
# That's all!