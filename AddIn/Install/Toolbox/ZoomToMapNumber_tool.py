# -*- coding: utf-8 -*-
"""
Created on Tue Dec 19 15:43:00 2017

@author: bwilson
"""
from __future__ import print_function
import os
import arcpy
from arcpy import mapping as MAP
import zoomToMapNumber
from ormap_utilities import ORMapLayers, get_dataframe, get_layer, list_mapnumbers

class ZoomToMapNumber(object):
    """This class has the methods you need to define
       to use your code as an ArcGIS Python Tool."""
        
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = self.__class__.__name__
        self.description = """Zoom to a map number."""
        self.canRunInBackground = False
        #self.category = "Map production" # Use your own category here, or an existing one.
        #self.stylesheet = "" # I don't know how to use this yet.
        self.mxdname = "CURRENT"        
        
    def getParameterInfo(self):
        """Define parameter definitions
           Refer to http://resources.arcgis.com/en/help/main/10.2/index.html#/Defining_parameters_in_a_Python_toolbox/001500000028000000/
           For datatype see https://desktop.arcgis.com/en/arcmap/latest/analyze/creating-tools/defining-parameter-data-types-in-a-python-toolbox.htm
        """
        map_number = arcpy.Parameter(name="mapnumber",
                                 displayName="Map Number",
                                 datatype="GPString",
                                 parameterType="Required", # Required|Optional|Derived
                                 direction="Input", # Input|Output
                                 multiValue=False, # We can accept many numbers.
                                )
        map_number.value = ""
        try:
            mxd = MAP.MapDocument(self.mxdname)
            df = get_dataframe(mxd, ORMapLayers.MainDF)
            layer = get_layer(mxd, df, ORMapLayers.MAPINDEX_LAYER)
            # Using the datasource instead of the layer avoids problems if there is a definition query.
            map_number.filter.list = list_mapnumbers(layer.dataSource, ORMapLayers.MapNumberField)
            map_number.value = map_number.filter.list[0]
            del mxd
        except Exception as e:
            arcpy.AddMessage("%s. \"%s\"" % (e,self.mxdname))

        return [map_number]

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        
        mapnum = parameters[0].valueAsText           
        if mapnum[-1] == "*":
            if not mapnum in parameters[0].filter.list:
                parameters[0].filter.list.append(mapnum)
            parameters[0].clearMessage()        
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""

        return

    def execute(self, parameters, messages):
        """The source code of your tool."""
        
        # Let's dump out what we know here.
        messages.addMessage("Running the ZoomToMapNumber tool.")
        for param in parameters:
            messages.addMessage("Parameter: %s = %s" % (param.name, param.valueAsText) )

        mxd = MAP.MapDocument(self.mxdname)
        messages.addMessage("MXD file: %s" % mxd.filePath)
        map_number = parameters[0].valueAsText
        zoomToMapNumber.update_page_layout(mxd, map_number)
        del mxd
        return
    
# =============================================================================
if __name__ == "__main__":
    # Unit tests, a few anyway.
    
    class Messenger(object):
        def addMessage(self, message):
            print(message)

    mxdname   = "TestMap.mxd"
    
    #mxd = MAP.MapDocument(mxdname)
    #df = get_dataframe(mxd, ORMapLayers.MainDF)
    #print(df.name)
    #layer = get_layer(mxd, df, ORMapLayers.MAPINDEX_LAYER)
    #print(layer.dataSource)
    ## Using the datasource instead of the layer itself avoids 
    ## problems with a definition query.
    #l = list_mapnumbers(layer.dataSource, "MapNumber")
    #print(l)
    #del mxd

    # This is only a test.
    zoomo = ZoomToMapNumber()
    zoomo.mxdname = mxdname # Override "CURRENT" for standalone test
    params = zoomo.getParameterInfo()
    params[0].value = "8.10.25"
    zoomo.execute(params, Messenger())
# That's all!
