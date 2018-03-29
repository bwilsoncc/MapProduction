# -*- coding: utf-8 -*-
"""
Wrappers for ESRUI arcpy functions to make them more usable.
@author: Brian Wilson <bwilson@co.clatsop.or.us>
"""
from __future__ import print_function
import os
import arcpy
from arcpy import mapping as MAP

def aprint(msg):		
    """ Print a message. Execution does not stop. """		
    #print(msg)		    # not needed with visual studio
    #sys.stdout.flush()		
    arcpy.AddMessage(msg)		

def eprint(msg):		
    """ Print a message. Execution will stop when you use this one. """		
    #print("ERROR:",msg) # not needed with visual studio	
    arcpy.AddError(msg)	

def DeleteFC(fc):
    """ Delete a feature class if it exists. """
    msg = "Feature class '%s'" % fc
    if arcpy.Exists(fc):
        arcpy.Delete_management(fc)
        msg += " deleted."
    aprint(msg)
    return	

def AddField(fc, fieldname, fieldtype, fieldlen=20):
    """ Add a field to a featureclass if it does not already exist.
    fc         name of featureclass
    fieldname  name of field to add
    fieldttype type of field (string) {TEXT|LONG}
    fieldlen   optional length of text field, defaults to 20
    """
    rval = True
    try:
        arcpy.AddField_management(fc, fieldname, fieldtype, field_length = fieldlen)
    except Exception as e:
        print(e)
        rval = False
    return rval

def ListFieldNames(fc):
    """ Return a list of the names of the fields in a feature class. """
    return [f.name for f in arcpy.ListFields(fc)]

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

def SetDefinitionQuery(mxd, df, layername, query):
    """ Set the definition query on a layer. """
    if df:
        layer = GetLayer(mxd, df, layername)
        if not layer: return False
        try:
            layer.definitionQuery = query
        except Exception as e:
            aprint("Can't set query \"%s\" on layer \"%s\"/\"%s\". \"%s\"" % (query, df.name, layername, e))
            return False
    return True
 
def ListPagenames(mxd):
    """ Given an mxd for a map document with Data Driven Pages,
    Return a list of pagenames from that doc. """
    try:
        maindf = mxd.dataDrivenPages.dataFrame
        ddp_layer = mxd.dataDrivenPages.indexLayer
    except Except as e:
        aprint("Can't get ddp layer, %s" % e)
    pagename = mxd.dataDrivenPages.pageNameField
    d_val = {}
    # Using the datasource instead of the layer avoids problems if there is a definition query.
    with arcpy.da.SearchCursor(ddp_layer.dataSource, [pagename.name]) as cursor:
        for row in cursor:
            d_val[row[0]] = 1
    return sorted(d_val)

# ---------------------------------------------------------------------

if __name__ == "__main__":

    workfolder = "C:\\GeoModel\\Clatsop\\Workfolder"
    mxdname = os.path.join(workfolder, "TestMap.mxd") # Often set to "CURRENT"
    if os.path.exists(mxdname):
        dfname = "MapView"
        layername = "MapIndex"
        mxd = MAP.MapDocument(mxdname)
        df = GetDataframe(mxd, dfname)
        layer = GetLayer(mxd, df, layername)
        aprint("layer.dataSource=%s"%layer.dataSource)

        lst = ListPagenames(mxd)
        aprint(lst)

        del mxd
    
    arcpy.env.workspace = "C:\\GeoModel\\MapProduction\\ORMAP_Clatsop_Schema.gdb\\TaxlotsFD"
    if arcpy.Exists("Taxlot"):
        l = ListFieldNames("Taxlot")
        print(l)

    aprint("Unit test aprint")
    eprint("Unit test eprint")      

    arcpy.env.workspace = os.path.join(workfolder, "ORMAP_Clatsop.gdb\\TaxlotsFD")
    if arcpy.Exists("MapIndex"):
#        AddField("MapIndex", "PageNumber", "LONG")
#        AddField("MapIndex", "PageName",   "TEXT", fieldlen=50)
        l = ListFieldNames("MapIndex")
        print(l)

    print("Tests completed.")
# That's all
