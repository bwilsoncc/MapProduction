# -*- coding: utf-8 -*-
"""
Created on Tue Dec 19 15:43:00 2017
@author: Brian Wilson <bwilson@co.clatsop.or.us>
"""
from __future__ import print_function
import os
import arcpy
from arcpy import mapping as MAP
from printMaps import print_maps
from arc_utilities import ListPagenames

class PrintMaps(object):
    """This class has the methods you need to define
       to use your code as an ArcGIS Python Tool."""
        
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = self.__class__.__name__
        self.description = """Print one or more maps, as determined by a list of map numbers."""
        self.canRunInBackground = False
        #self.category = "Map production" # Use your own category here, or an existing one.
        #self.stylesheet = "" # I don't know how to use this yet.
        self.mxdname = "CURRENT"
        self.extensions = ["pdf","jpg"]
        return

    def __set_output_filter(self, format):
        if format == "PDF":
            filter = [ "pdf" ]
        elif format == "JPEG":
            filter = [ "jpg" ]
        else:
            filter = [ "*" ]
        return filter
        
    def __set_output_file(self, currentpathname, format):
        """Build a new output file name based on current parameter settings,
        and set it in the "parameters" list. """ 

        path = fileext = newfilename = ""
        if currentpathname: 
            if os.path.isdir(currentpathname):
                # This is just a directory, leave the filename empty
                path = currentpathname
            else:
                # We've got a filename, pull it off the path.
                path,fileext = os.path.split(currentpathname)

        file = ext = ""
        if fileext:
            file,ext = os.path.splitext(fileext)
        else:
            file = "tp"

        if format == "PDF":
            fileext = file + ".pdf"
        elif format == "JPEG":
            fileext = file + ".jpg"
        else:
            fileext = file

        newfilename = os.path.normpath(os.path.join(path, fileext))
        return newfilename
    
    def getParameterInfo(self):
        """Define parameter definitions and return them as a list.
        """
        # params[0] is map number list (delimited by ";")
        map_number = arcpy.Parameter(name="map_number",
                                     displayName="Map Number",
                                     datatype="GPString",
                                     parameterType="Required", # Required|Optional|Derived
                                     direction="Input", # Input|Output
                                     multiValue = True,
                                     )
        map_number.filter.type = "ValueList"
        map_number.filter.list = []
        mxd_filepath = ""
        try:
            mxd = MAP.MapDocument(self.mxdname)
            map_number.filter.list = ListPagenames(mxd)
            mxd_filepath = os.path.split(mxd.filePath)[0]
            del mxd
        except Exception as e:
            arcpy.AddMessage("%s. \"%s\"" % (e,self.mxdname))

                
        # params[1] is output format
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
        
        # params[2] is output file
        output_file = arcpy.Parameter(name="output_file",
                                      displayName="Output file",
                                      datatype="DEFile",
                                      parameterType="Required", # Required|Optional|Derived
                                      direction="Output", # Input|Output
                                      )
        output_file.filter.list = self.__set_output_filter(str(output_format.value))

        # Try to set up something more useful as a path than the default
        output_file.value = self.__set_output_file(mxd_filepath, output_format.value)

        return [map_number, output_format, output_file]
        
    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""

        parameters[2].filter.list = self.__set_output_filter(str(parameters[1].value))
        parameters[2].value = self.__set_output_file(str(parameters[2].value), parameters[1].value)

        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of your tool."""
        
        # Let's dump out what we know here.
        messages.addMessage("Printing maps.")
        #for param in parameters:
        #    messages.addMessage("Parameter: %s = %s" % (param.name, param.valueAsText) )
        
        # Get the parameters from our parameters list,
        # then call a generic python function.
        #
        # This separates the code doing the work from all
        # the crazy code required to talk to ArcGIS.
                
        # See http://resources.arcgis.com/en/help/main/10.2/index.html#//018z00000063000000
        map_numbers = parameters[0].valueAsText
        output_type = parameters[1].valueAsText
        output_file = parameters[2].value
        
        # Okay finally go ahead and do the work.
        mxd = MAP.MapDocument(self.mxdname)
        print_maps(mxd, map_numbers, output_type, str(output_file))
        del mxd

        return

# =============================================================================
if __name__ == "__main__":
    # Unit tests, a few anyway.
    
    class Messenger(object):
        def addMessage(self, message):
            print(message)

    mxdname = "C:/GeoModel/Clatsop/Workfolder/TestMap.mxd"
    pmo = PrintMaps()
    pmo.mxdname = mxdname # Override "CURRENT" for standalone test
    params = pmo.getParameterInfo()
    params[0].value = "8 10 5CD D2;8 10 5CD D1;8 10 5CD"
    params[1].value = "JPEG"
    params[2].value = r"C:\TempPath\printmap-unittest-.jpg"
    pmo.execute(params, Messenger())

# That's all!
