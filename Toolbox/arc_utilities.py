# -*- coding: utf-8 -*-
#
#  Wrappers for ESRUI arcpy functions to make them more usable.
#  Written by bwilson for Clatsop County GIS
#
from __future__ import print_function
import sys
from arcpy import AddMessage, AddError, Exists, Delete_management
from arcpy import mapping as MAP

def aprint(msg):		
    """ Print a message. Execution does not stop. """		
    print(msg)		
    sys.stdout.flush()		
    AddMessage(msg)		
		
def eprint(msg):		
    """ Print a message. Execution will stop when you use this one. """		
    print("ERROR:",msg)		
    AddError(msg)	

def deletefc(fc):
    """ Delete a feature class if it exists. """
    msg = "Feature class '%s'" % fc
    if Exists(fc):
        Delete_management(fc)
        msg += " deleted."
    aprint(msg)
    return	
		
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
    except IndexError:		
        print("Can't find layer \"%s\"/\"%s\"." % (df.name, layername))		
    return layer
 
if __name__ == "__main__":

    mxdname = "TestMap.mxd" # Often set to "CURRENT"
      		
    aprint("Unit test aprint")
    eprint("Unit test eprint")      

    dfname = "MapView"
    layername = "MapIndex"
    mxd = MAP.MapDocument(mxdname)
    df = get_dataframe(mxd, dfname)
    layer = get_layer(mxd, df, layername)
    aprint("layer.dataSource=%s"%layer.dataSource)		
         
    del mxd
    
# That's all
