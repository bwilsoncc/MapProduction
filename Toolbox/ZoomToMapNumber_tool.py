# -*- coding: utf-8 -*-
"""
Created on Tue Dec 19 15:43:00 2017

@author: bwilson
"""
from __future__ import print_function
import arcpy
import zoomToMapNumber

class ZoomToMapNumber(object):
    """This class has the methods you need to define
       to use your code as an ArcGIS Python Tool."""
        
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "ZoomToMapNumber"
        self.description = """Zoom to a map number."""
        self.canRunInBackground = False
        self.category = "ORMap" # Use your own category here, or an existing one.
        #self.stylesheet = "" # I don't know how to use this yet.
        
    def getParameterInfo(self):
        """Define parameter definitions
           Refer to http://resources.arcgis.com/en/help/main/10.2/index.html#/Defining_parameters_in_a_Python_toolbox/001500000028000000/
           For datatype see https://desktop.arcgis.com/en/arcmap/latest/analyze/creating-tools/defining-parameter-data-types-in-a-python-toolbox.htm
        """
        
        # You can define a tool to have no parameters
        params = []
    
        # ..or you can define a parameter
        input_fc = arcpy.Parameter(name="mapnumber",
                                 displayName="Map Number",
                                 datatype="GPString",
                                 parameterType="Required", # Required|Optional|Derived
                                 direction="Input", # Input|Output
                                )
        # You can set filters here for example
        #input_fc.filter.list = ["Polygon"]
        # You can set a default if you want -- this makes debugging a little easier.
        input_fc.value = "8.10.25"
         # ..and then add it to the list of defined parameters
        params.append(input_fc)

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
        messages.addMessage("Running the ZoomToMapNumber tool.")
        for param in parameters:
            messages.addMessage("Parameter: %s = %s" % (param.name, param.valueAsText) )
        
        # Get the parameters from our parameters list,
        # then call a generic python function.
        #
        # This separates the code doing the work from all
        # the crazy code required to talk to ArcGIS.

        mxdname = "CURRENT"        
        # See http://resources.arcgis.com/en/help/main/10.2/index.html#//018z00000063000000
        map_number = parameters[0].valueAsText
        zoomToMapNumber.update_page_layout(mxdname, map_number)
        return

# That's all!
