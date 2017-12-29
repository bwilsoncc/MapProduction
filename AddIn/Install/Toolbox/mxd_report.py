# -*- coding: utf-8 -*-
"""
Created on Dec 29 09:38

Borrowed from the ESRI "ElementReport.py" script.

@author: bwilson
"""
from __future__ import print_function
from arcpy import mapping as MAP
import os, sys
from datetime import datetime

def header(mxd):
    print("PageLayout Report\t", datetime.today().strftime("%B %d, %Y"))
    print(mxd.filePath)
    print()

def dataframes(mxd):
    # Use the list of data frames so report order will be correct.
    l_df = MAP.ListDataFrames(mxd)
    print(" DATA FRAMES:")
    for df in l_df:
        elm = MAP.ListLayoutElements(mxd, wildcard=df.name)[0]
        print("\t Name:                " + elm.name )
        print("\t X Position:          " + str(elm.elementPositionX) )
        print("\t Y Position:          " + str(elm.elementPositionY) )
        print("\t Height:              " + str(elm.elementHeight) )
        print("\t Width:               " + str(elm.elementWidth) )
        print()
    
def element(mxd, element_name):
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
    header(mxd)
    dataframes(mxd)
    for e in ["TEXT_ELEMENT", 
              "PICTURE_ELEMENT", 
              "GRAPHIC_ELEMENT",
              "MAPSURROUND_ELEMENT",
              "LEGEND_ELEMENT"]:
        element(mxd,e)
    
if __name__ == "__main__":

    mxdname = "TestMap.mxd"
    mxd = MAP.MapDocument(mxdname)
    report(mxd)
    del mxd
    
# That's a;;!

