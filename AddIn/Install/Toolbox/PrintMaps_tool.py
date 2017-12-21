# -*- coding: utf-8 -*-
"""
Created on Tue Dec 19 15:43:00 2017

@author: bwilson
"""
from __future__ import print_function
import os
import arcpy
from arcpy import mapping as MAP
import printMaps
from ormap_utilities import ORMapLayers, get_dataframe, get_layer, list_mapnumbers

class PrintMaps(object):
    """This class has the methods you need to define
       to use your code as an ArcGIS Python Tool."""
        
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "PrintMaps"
        self.description = """Print one or more maps, as determined by a list of map numbers."""
        self.canRunInBackground = False
        self.category = "ORMap" # Use your own category here, or an existing one.
        #self.stylesheet = "" # I don't know how to use this yet.
        self.extensions = ["pdf","jpg"]
        return
    
    def getParameterInfo(self):
        """Define parameter definitions
           Refer to http://resources.arcgis.com/en/help/main/10.2/index.html#/Defining_parameters_in_a_Python_toolbox/001500000028000000/
           For datatype see https://desktop.arcgis.com/en/arcmap/latest/analyze/creating-tools/defining-parameter-data-types-in-a-python-toolbox.htm
        """
        
        # You can define a tool to have no parameters
        params = []

        mxd = MAP.MapDocument("CURRENT")
    
        # ..or you can define a parameter
        map_number = arcpy.Parameter(name="map_number",
                                     displayName="Map Number",
                                     datatype="GPString",
                                     parameterType="Required", # Required|Optional|Derived
                                     direction="Input", # Input|Output
                                     multiValue = True,
                                     )
        # You can set filters here for example
        map_number.filter.type = "ValueList"
        
        df = get_dataframe(mxd, ORMapLayers.MainDF)
        layer = get_layer(mxd, df, ORMapLayers.MAPINDEX_LAYER)
        # Using the datasource instead of the layer avoids problems if there is a definition query.
        map_number.filter.list = list_mapnumbers(layer.dataSource, ORMapLayers.MapNumberField)
        # You can set a default if you want -- this makes debugging a little easier.
        #map_number.value = map_number.filter.list[0]
        
        params.append(map_number)

        output_format = arcpy.Parameter(name="output_format",
                                        displayName="Output format",
                                        datatype="GPString",
                                        parameterType="Required", # Required|Optional|Derived
                                        direction="Input", # Input|Output
                                        )
        # You could set a list of acceptable values here for example
        output_format.filter.type = "ValueList"
        output_format.filter.list = ["Printer","PDF","JPEG"]
        # You can set a default value here.
        output_format.value = "PDF"
        params.append(output_format)
        
        output_file = arcpy.Parameter(name="output_file",
                                      displayName="Output file",
                                      datatype="DEFile",
                                      parameterType="Required", # Required|Optional|Derived
                                      direction="Output", # Input|Output
                                      )
      
        # Try to set up something more useful as a path than the default
        path,fileext = os.path.split(mxd.filePath)
        file,ext = os.path.splitext(fileext)
        output_file.value = path
        output_file.filter.list = self.extensions
        params.append(output_file)
        
        del mxd
        return params

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""

        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of your tool."""
        
        # Let's dump out what we know here.
        messages.addMessage("Printing maps.")
        for param in parameters:
            messages.addMessage("Parameter: %s = %s" % (param.name, param.valueAsText) )
        
        # Get the parameters from our parameters list,
        # then call a generic python function.
        #
        # This separates the code doing the work from all
        # the crazy code required to talk to ArcGIS.
        
        mxdname = "CURRENT"
        
        # See http://resources.arcgis.com/en/help/main/10.2/index.html#//018z00000063000000
        map_numbers = parameters[0].valueAsText
        output_type = parameters[1].valueAsText
        output_file = parameters[2].value
        
        # Okay finally go ahead and do the work.
        printMaps.print_maps(mxdname, map_numbers, output_type, output_file)
        return

# =============================================================================
        
if __name__ == "__main__":
    # Unit tests, a few anyway.
    
    # Normally this is set to CURRENT        
    mxdname   = "TestMap.mxd"
    mxd = MAP.MapDocument(mxdname)
    
    df = get_dataframe(mxd, ORMapLayers.MainDF)
    print(df.name)
    
    layer = get_layer(mxd, df, ORMapLayers.MAPINDEX_LAYER)
    print(layer.dataSource)
    
    # Using the datasource instead of the layer itself avoids 
    # problems with a definition query.
    l = list_mapnumbers(layer.dataSource, "MapNumber")
    print(l)
    
    del mxd

    pmo = PrintMaps()
    
    # We don't really print anything here, sorry.
    # This is only a test.

# That's all!
