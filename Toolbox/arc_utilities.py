# -*- coding: utf-8 -*-
#
#  Wrappers for ESRUI arcpy functions to make them more usable.
#  Written by bwilson for Clatsop County GIS
#
from __future__ import print_function
import sys
from arcpy import AddMessage, AddError, Exists, Delete_management, ListFields
from arcpy import mapping as MAP

def aprint(msg):		
    """ Print a message. Execution does not stop. """		
    #print(msg)		    # not needed with visual studio
    #sys.stdout.flush()		
    AddMessage(msg)		
		
def eprint(msg):		
    """ Print a message. Execution will stop when you use this one. """		
    #print("ERROR:",msg) # not needed with visual studio	
    AddError(msg)	

def DeleteFC(fc):
    """ Delete a feature class if it exists. """
    msg = "Feature class '%s'" % fc
    if Exists(fc):
        Delete_management(fc)
        msg += " deleted."
    aprint(msg)
    return	
		
def ListFieldNames(fc):
    """ Return a list of the names of the fields in a feature class. """
    return [f.name for f in ListFields(fc)]

def GetDataframe(mxd, dfname):		
    """ Return the named dataframe object from an MXD. """		
    df = None		
    try:		
        df = MAP.ListDataFrames(mxd, dfname)[0]		
    except Exception as e:		
        aprint("Dataframe not found. Make sure it is named '%s'. \"%s\"" % (dfname,e))		
    return df		
		
def GetLayer(mxd, df, layername):
    """ Return the named layer from an MXD. """
    layer = None		
    try:		
        layer = MAP.ListLayers(mxd, layername, df)[0]		
    except IndexError:		
        print("Can't find layer \"%s\"/\"%s\"." % (df.name, layername))		
    return layer
 
if __name__ == "__main__":

    mxdname = "TestMap.mxd" # Often set to "CURRENT"

    arcpy.env.workspace = "C:\\GeoModel\\MapProduction\\ORMAP_Clatsop_Schema.gdb\\TaxlotsFD"
    l = ListFieldNames("Taxlot")
    print(l)
      		
    aprint("Unit test aprint")
    eprint("Unit test eprint")      

    dfname = "MapView"
    layername = "MapIndex"
    mxd = MAP.MapDocument(mxdname)
    df = GetDataframe(mxd, dfname)
    layer = GetLayer(mxd, df, layername)
    aprint("layer.dataSource=%s"%layer.dataSource)		
         
    del mxd
    
# That's all
