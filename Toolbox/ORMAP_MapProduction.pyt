# -*- coding: utf-8 -*-
"""
ORMap Map Production python toolbox
Created on Tue Dec 19 15:43:00 2017
@author: Brian Wilson <bwilson@co.clatsop.or.us>
"""
from __future__ import print_function
import arcpy

__version__ = "4"

# Import all the tool classes that will be included in this toolbox.
from ormap.ZoomToMapNumber_tool import ZoomToMapNumber
from ormap.PrintMaps_tool import PrintMaps
from ormap.MXDReport_tool import MXDReport

class Toolbox(object):
    def __init__(self):
        """Define the toolbox (the name of the toolbox is the name of this .pyt file)."""
        self.label = "ORMap Map Production Toolbox v%s" % __version__
        self.alias = ""
        self.description = """Toolbox containing ORMap Map Production tools."""

        # List of tool classes associated with this toolbox
        self.tools = [
                     ZoomToMapNumber,
                     PrintMaps,
                     MXDReport
                     ]

if __name__ == "__main__":
    # Running this as a standalone script tells me about the toolbox.
    toolbox = Toolbox()
    print("toolbox:",toolbox.label)
    print("description:",toolbox.description)
    print("tools:")
    for t in toolbox.tools:
        tool = t()
        print('  ',tool.label)
        print('   description:', tool.description)
        for param in tool.getParameterInfo():
            print('    ', param.name, ':', param.displayName)

# That's all!
