# -*- coding: utf-8 -*-
"""
Created on Mon Dec 18 09:54:02 2017
@author: Brian Wilson <bwilson@co.clatsop.or.us>
"""
from __future__ import print_function
import xlrd
import re
from collections import defaultdict

def make_sortable(taxlotno):
    """ Given a taxlot number, reformat it into an ASCII sortable value. """
    sortable = ""
    mo = re.search(r'(\d*)(.*)', taxlotno)
    if mo:
        n = mo.group(1)
        if not n: n = "0"
        s = mo.group(2)
        sortable = "%06d%s" % (int(n),s.strip())
    return sortable

class cancellations(object):
    """ I made this into an object so that it could read the spreadsheet and then use a cached copy of it. """

    d_cancelled = defaultdict(list) # indexed by mapnum, containing lists of taxlots

    def __init__(self, xlsfile = "K:\\taxmaped\\Clatsop\\towned\\cancelled.xlsx"):
        self.read_xls(xlsfile)
        return

    def read_xls(self, xlfile):
        """ Loads cancelled taxlot numbers into an internal table. 
 Assumes the Excel file has its data in the first
 two columns (mapnum,cancelled_taxlot) in its first worksheet. """
        d_sortable = {} # Use a dict to squash duplicates
        wb = xlrd.open_workbook(xlfile)
        #print(wb.get_sheet_names()[0])
        ws = wb.sheet_by_index(0)
        for row_index in range(1, ws.nrows): # Skip column headers
            mapnum = ws.cell(row_index, 0).value
            if mapnum:
                taxlot = ws.cell(row_index, 1).value.strip()
                self.d_cancelled[mapnum].append(taxlot)

    def get_list(self, mapnum):
        """ Returns the (sorted) list of taxlots for a given map number. 
        Note that mapnum has to be in dotted format T.R.Sqq, eg 8.9.10AB """
        try:
            l = self.d_cancelled[mapnum]
        except KeyError:
            return None
        d_sortable = {} # This will nuke duplicate taxlots.
        for taxlot in l:
            d_sortable[make_sortable(taxlot)] = taxlot
        # This will return the list of taxlots (not the list of "sortable" taxlots)
        return [d_sortable[k] for k in sorted(d_sortable)]   

# =============================================================================
if __name__ == "__main__":
    # unit tests
    can = cancellations()
    for mapnum in ["8.10.8BB", "8.10.8", "8.10.25"]:
        lst = can.get_list(mapnum)
        print(mapnum, "returned", len(lst))
        print(lst)
        print()

    print("Unit tests completed.")
# That's all!
