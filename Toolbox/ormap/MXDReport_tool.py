# -*- coding: utf-8 -*-
"""
Created on Fri Dec 29 11:31:52 2017

@author: bwilson
"""
from __future__ import print_function
import os, sys
import arcpy
from arcpy import mapping as MAP
from mxd_report import report

# =============================================================================
class MXDReport(object):
    """This class has the methods you need to define
       to use your code as an ArcGIS Python Tool."""
        
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = self.__class__.__name__
        self.description = """Generate a report on an MXD file."""
        self.canRunInBackground = False
        #self.category = "Map production" # Use your own category here, or an existing one.
        #self.stylesheet = "" # I don't know how to use this yet.
        
    def getParameterInfo(self):
        """Define parameter definitions
           Refer to http://resources.arcgis.com/en/help/main/10.2/index.html#/Defining_parameters_in_a_Python_toolbox/001500000028000000/
           For datatype see https://desktop.arcgis.com/en/arcmap/latest/analyze/creating-tools/defining-parameter-data-types-in-a-python-toolbox.htm
        """

        mxdname = arcpy.Parameter(name="map document",
                                 displayName="Map document name",
                                 datatype=["DEMapDocument","GPString"],
                                 parameterType="Required", # Required|Optional|Derived
                                 direction="Input", # Input|Output
                                )
        mxdname.value = "CURRENT"

        output = arcpy.Parameter(name="output_file",
                                 displayName="Output document name",
                                 datatype="DEFile",
                                 parameterType="Required", # Required|Optional|Derived
                                 direction="Output", # Input|Output
                                )
        output.filter.list = [ "txt" ]
        output.value = "C:\\TempPath\output.txt"

        return [mxdname,output]

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def get_txt_name(self, mxdname):
        if mxdname == "CURRENT":
            try:
                mxd = MAP.MapDocument(mxdname)
                mxdname = mxd.filePath
                del mxd
            except NameError:
                mxdname = ""
        if mxdname:
            (path,nameext) = os.path.split(mxdname)
            (name,ext) = os.path.splitext(nameext)
            return os.path.join(path, name + '.txt')
        return ""
    
    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        
        # Has the user altered the output location already?
        # No - so make a new one up based on the mxdname.
        if not parameters[1].altered:
            parameters[1].value = self.get_txt_name(parameters[0].valueAsText)
        
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        mxdname = parameters[0].valueAsText 
        output  = parameters[1].valueAsText
        
        mxd = MAP.MapDocument(mxdname)
        messages.addMessage("MXD file: %s" % mxd.filePath)

        fp = open(output, "w")
        original = sys.stdout
        sys.stdout = fp 
    
        report(mxd)

        del mxd
        
        sys.stdout.flush()
        sys.stdout = original
        os.startfile(output)
        return  

# =============================================================================
if __name__ == "__main__":
    # Unit tests, a few anyway.
    
    class Messenger(object):
        def addMessage(self, message):
            print(message)

    mxdname = "C:\\GeoModel\\Clatsop\\Workfolder\\TestMap.mxd"
    output  = "C:\\TempPath\\TestMap_report.txt"

    repo = MXDReport()
    repo.mxdname = mxdname # Override "CURRENT" for standalone test
    params = repo.getParameterInfo()
    params[0].value = mxdname
    params[1].value = output
    repo.execute(params, Messenger())

    print("Unit test completed.")
    
# That's all!
