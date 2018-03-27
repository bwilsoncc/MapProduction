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
 
# ---------------------------------------------------------------------
def dump_fields():
    with open("s.csv","w") as fp:
        for t in [
                ("taxmapan", "taxmapanno"),
                ("taxlotan", "taxlotanno"),
                ("taxcodan", "taxcodanno"),
                ]:
            for ws in t:
                print("workspace:", ws)
                arcpy.env.workspace = os.path.join("C:\\GeoModel\\Clatsop\\Workfolder\\t4-6", ws)
                for fc in ["annotation.igds", "arc", "point"]:
                    if arcpy.Exists(fc):
                        l = ListFieldNames(fc)
                        ls = [str(item) for item in l]
                        rval = "%s, %s" % (ws, fc)
                        for item in ls:
                            rval += ", %s" %item
                        print(rval)
                        rval += "\n"
                        fp.write(rval)

    return

if __name__ == "__main__":
    
    dump_fields()

    arcpy.env.workspace = "C:\\GeoModel\\MapProduction\\ORMAP_Clatsop_Schema.gdb\\TaxlotsFD"
    if arcpy.Exists("Taxlot"):
        l = ListFieldNames("Taxlot")
        print(l)

        aprint("Unit test aprint")
        eprint("Unit test eprint")      

    arcpy.env.workspace = "C:\\GeoModel\\Clatsop\\Workfolder\\ORMAP_Clatsop.gdb\\TaxlotsFD"
    if arcpy.Exists("MapIndex"):
        AddField("MapIndex", "PageNumber", "LONG")
        AddField("MapIndex", "PageName",   "TEXT", fieldlen=50)
        l = ListFieldNames("MapIndex")
        print(l)

    mxdname = "TestMap.mxd" # Often set to "CURRENT"
    if os.path.exists(mxdname):
        dfname = "MapView"
        layername = "MapIndex"
        mxd = MAP.MapDocument(mxdname)
        df = GetDataframe(mxd, dfname)
        layer = GetLayer(mxd, df, layername)
        aprint("layer.dataSource=%s"%layer.dataSource)
        del mxd
  
# That's all
