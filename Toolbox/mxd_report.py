# -*- coding: utf-8 -*-
"""
Created on Dec 29 09:38

Borrowed from the ESRI "ElementReport.py" script.

@author: bwilson
"""
from __future__ import print_function
import arcpy
from arcpy import mapping as MAP
from datetime import datetime

def header(mxd):
    print("MXD Report\t", datetime.today().strftime("%B %d, %Y"))
    print(mxd.filePath)
    print()

def show_layer(lyr):
    # Show ONLY layers with a query.
    #if not(lyr.supports("DEFINITIONQUERY") and lyr.definitionQuery): return

    rcount = 0

    space = True
    isfeature = False
    isgroup   = False
    
    msg = "\t"
    if lyr.isBroken:
        msg += "BROKEN "
    if lyr.isGroupLayer:
        msg += "Group "
        isgroup = True
    elif lyr.isBasemapLayer:
        msg += "Basemap "
    elif lyr.isFeatureLayer:
        msg += "Feature "
        isfeature = True
    else:
        msg += "    "
        space = False
        
    islabel = False # Is this a word? :-)
    if lyr.supports("LABELCLASSEs"): islabel = True

        
    print(msg+"Layer: %s" % lyr.longName)

    if lyr.supports("DATASOURCE"):

#        # A hack to repair the anno template
#        oldp = "C:\\GeoModel\\Clatsop\\convertii"
#        newp = "C:\\GeoModel\\Clatsop\\Workfolder"
#        if lyr.dataSource.find(oldp)==0:
#            try:
#                lyr.findAndReplaceWorkspacePath(oldp, newp, validate=False)
#                print("\t Source has been set to %s" % lyr.dataSource)
#                rcount = 1
#            except ValueError:
#                print("Replace failed, %s => %s" % (oldp, newp))
            
        print("\t%s" % lyr.dataSource)
        
    if lyr.supports("SHOWLABELS"): 
            print("\tShow labels: ON")
    
    if not lyr.visible: 
        #print("\tVisible: NO")
        pass
    
    if lyr.supports("DEFINITIONQUERY") and lyr.definitionQuery:
        #print("\tQuery: %s" % lyr.definitionQuery)
        pass
        
    if space: print()
    
    return rcount

def show_layers(mxd, df):
    print("    Layers:")
    rcount = 0
    for lyr in MAP.ListLayers(mxd, "", df):
        rcount += show_layer(lyr)
    print()
    return rcount
    
def show_dataframes(mxd):
    # Use the list of data frames so report order will be correct.
    l_df = MAP.ListDataFrames(mxd)
    rcount = 0
    print(" DATA FRAMES:")
    for df in l_df:
        elm = MAP.ListLayoutElements(mxd, wildcard=df.name)[0]
        print("    Dataframe:           " + elm.name)
        print("    X Position:          " + str(elm.elementPositionX))
        print("    Y Position:          " + str(elm.elementPositionY))
        print("    Height:              " + str(elm.elementHeight))
        print("    Width:               " + str(elm.elementWidth))
        print()
        
        rcount += show_layers(mxd, df)
    return rcount
    
def show_layout_element(mxd, element_name):
    
    l_elm = MAP.ListLayoutElements(mxd, element_name)
    if len(l_elm) > 0:
        print(" %s:" % element_name.replace('_',' '))
        # Sorted by "name" property
        for elm in sorted(l_elm, key=lambda x: x.name):
            print("\t Name:               ", elm.name)
            if elm.type == "LEGEND_ELEMENT" or elm.type == "MAPSURROUND_ELEMENT":
                print("\t Parent data frame:  ", elm.parentDataFrameName)
            if elm.type == "LEGEND_ELEMENT":
                print("\t Title:              ", elm.title)
            if elm.type == "PICTURE_ELEMENT":
                print("\t Source image:       ",elm.sourceImage)
            if elm.type == "TEXT_ELEMENT":
            # Todo - fix indent on multiline?
                print("\t Text string:        ",elm.text )
                print("\t Angle:              ",elm.angle)
            print("\t X Position:         ",elm.elementPositionX)
            print("\t Y Position:         ",elm.elementPositionY)
            print("\t Height:             ",elm.elementHeight)
            print("\t Width:              ",elm.elementWidth)
            print()
        print()

def report(mxd):
    rcount = 0
    header(mxd)

    rcount = show_dataframes(mxd)
    return
    for e in ["TEXT_ELEMENT", 
              "PICTURE_ELEMENT", 
              "GRAPHIC_ELEMENT",
              "MAPSURROUND_ELEMENT",
              "LEGEND_ELEMENT",
              ""]:
        show_layout_element(mxd,e)
    return rcount

if __name__ == "__main__":

    gdb = "C:/GeoModel/Clatsop/ORMAP-SchemaN_08-21-08/ORMAP-SchemaN_08-21-08.mdb/TaxlotsFD"
    arcpy.env.workspace = gdb
    for anno in arcpy.ListFeatureClasses("", "ANNOTATION"):
        print(anno)
    pass

    mxdname = "TestMap.mxd"
    #mxdname = "C:/GeoModel/Clatsop/AnnoTemplate.mxd"
 
    mxd = MAP.MapDocument(mxdname)
    rcount = report(mxd)

    if rcount>0:
        print("MXD has been modified.")
        #mxd.save()
        pass
    del mxd
    
# That's a;;!

