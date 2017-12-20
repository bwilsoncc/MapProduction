# -*- coding: utf-8 -*-
"""
Created on Tue Dec 19 15:43:00 2017

@author: bwilson
"""
from __future__ import print_function
import arcpy
import printMaps

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
        
    def getParameterInfo(self):
        """Define parameter definitions
           Refer to http://resources.arcgis.com/en/help/main/10.2/index.html#/Defining_parameters_in_a_Python_toolbox/001500000028000000/
           For datatype see http://resources.arcgis.com/en/help/main/10.2/index.html#/Defining_parameter_data_types_in_a_Python_toolbox/001500000035000000/
        """
        
        # You can define a tool to have no parameters
        params = []
    
        # ..or you can define a parameter
        map_number = arcpy.Parameter(name="map_number",
                                 displayName="Map Number",
                                 datatype="GPString",
                                 parameterType="Required", # Required|Optional|Derived
                                 direction="Input", # Input|Output
                                )
        # You can set filters here for example
        #input_fc.filter.list = ["Polygon"]
        # You can set a default if you want -- this makes debugging a little easier.
        map_number.value = "8.10.8"
         # ..and then add it to the list of defined parameters
        params.append(map_number)
        

        # I think I want to define
        # output type PRINTER | PDF | JPEG
        # printer device or file name for PDF

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
        params.append(output_file)

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
        messages.addMessage("Printing a map.")
        for param in parameters:
            messages.addMessage("Parameter: %s = %s" % (param.name, param.valueAsText) )
        
        # Get the parameters from our parameters list,
        # then call a generic python function.
        #
        # This separates the code doing the work from all
        # the crazy code required to talk to ArcGIS.
        
        mxdname = "CURRENT"
        
        # See http://resources.arcgis.com/en/help/main/10.2/index.html#//018z00000063000000
        map_number  = parameters[0].valueAsText
        output_type = parameters[1].valueAsText
        output_file = parameters[2].value
        
        # Okay finally go ahead and do the work.
        printMaps.print_a_map(mxdname, map_number, output_type, output_file)
        return

# That's all!
