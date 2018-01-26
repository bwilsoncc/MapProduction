# -*- coding: utf-8 -*-
"""
Create the link between an annotation feature class and its linked feature class.

INSTRUCTIONS: In ArcMap,
  open the annotation attribute table,
  do "field calculate" on the FeatureId field,
  select "Show Codeblock"
  for the expression under "FeatureId=" put f( !MAPTAXLOT! )
  use "Load..." to load this code,
  select Python, (it ALWAYS switches to BASIC!)
  and run it.

Created on Thu Jan 25 13:42:13 2018

@author: Brian Wilson <bwilson@co.clatsop.or.us>
"""
import arcpy
d = {}
with arcpy.da.SearchCursor("Taxlot", ["OID@", "MAPTAXLOT"]) as cursor:
    for row in cursor: d[row[1]] = row[0]

def f(x):
    try:
        return d[x]
    except KeyError:
        pass
    return None
