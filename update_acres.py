# -*- coding: utf-8 -*-
"""
Created on Thu Jan 18 09:19:41 2018

@author: Brian Wilson <bwilson@co.clatsop.or.us>
"""
from __future__ import print_function
import os
import arcpy
import re

dryrun = False
re_acre = re.compile(r"([\d\.]*)(\\?\s*)(AC\.|AC)?", re.IGNORECASE)

# =============================================================================

def testreadfc(target, fc):
    fieldnames = ("*")
    try:
        rows = arcpy.da.SearchCursor(fc, fieldnames)
    except Exception as e:
        print("Can't read from %s; %s" % (fc, e))
        return
    for row in rows:
        print(row[0])
    del rows
    return

def write_featureclass(fc, fieldnames, where_clause=None):
    """ Update a column in a feature class with the value from another column.
    Pass in an array containing the source and destination columns.
    Column 1 should be text containing a specific pattern, see re_acre.
    Column 2 should be a double that will accept a converted text value.

    For testing you can set the global "dryrun" to True to bypass writes. 
    Also you can set the input to a Source/ coverage, 
    and use fieldnames TEXT, FID
    and set whereclause LEVEL=38
    """
    count = 0
    try:
        cursor = arcpy.da.UpdateCursor(fc, fieldnames, where_clause=where_clause)
    except Exception as e:
        print("Can't read from %s; %s" % (fc, e))
        return count
    #print(target, fc)
    for row in cursor:
#        print("%10s | %s | %s" % (target, row[1], row[0]))
        text = row[0]
        num  = row[1]
        acre = 0.0
        try:
            mo = re_acre.search(text)
            if mo:
                at = mo.group(1)
                if at: acre = float(at) # Empty number is okay, set to 0.0
                spc  = mo.group(2)
                sfx  = mo.group(3)
                print("%7.2f|%7.2f | %4s | \"%s\"| \"%s\"" % (acre,num, sfx, spc, text))
                count += 1
                row[1] = acre
                if not dryrun: cursor.updateRow(row)
            else:
                print("R: %s" % (text))

        except ValueError:
            print("Vs: %s" % (text))
                
        except Exception as e:
            print("E: %s \"%s\"" % (text, e))
            
    del cursor
    return count

def update_acres(fc):
    """ Convert the contents of the text acres field to a float and write it to the double field. """
    
    fields = ("TAXACRETXT", "TAXACRES")
    return write_featureclass(fc, fields)
    
# =============================================================================
if __name__ == "__main__":

    from glob import glob

    # Sure we can do a FC in an MDB...
    fc = r"C:\GeoModel\Clatsop\ORMAP-SchemaN_08-21-08.mdb\TaxlotsFD\MapIndex"
#    testreadfc(fc)

    # ...but how about a coverage?
    sourcefolder = "C:\GeoModel\Clatsop\Source"
    workfolder   = "C:\GeoModel\Clatsop\WorkFolder"
    os.chdir(workfolder)
    count = 0
    
    dryrun = True
    for target in glob(r"t[4-9]-*"):
        coverage = os.path.join(sourcefolder, target, "taxmap", "annotation.igds")
        wc = "LEVEL = 38"
        fields = ("TEXT","FID")
        
        coverage = os.path.join(workfolder, target, "taxacan", "annotation.igds")
        if not arcpy.Exists(coverage):
            print("No such coverage:", coverage)
            continue

        print(target)
        count += update_acres(coverage)
    print("That's all!", count)
# That's all!
