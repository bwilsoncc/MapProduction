# -*- coding: utf-8 -*-
"""
Created on Mon Dec 18 09:54:02 2017
@author: Brian Wilson <bwilson@co.clatsop.or.us>
"""
from __future__ import print_function
import xlrd
import re

# =============================================================================
def read_cancelled(xlfile, query_mapnum):
    """ Loads a list of cancelled taxlot numbers for a given map number. 
    Assumes the Excel file has its data in the first
    two columns (mapnum,canno) in its first worksheet. """
    
    # Make simple query into a regular expression
    regex = '^' + query_mapnum.replace('.','\.').replace("*","[ABCD]?[ABCD]?") + '$'
    #print(regex)
    d_sortable = {} # Use a dict to squash duplicates
    wb = xlrd.open_workbook(xlfile)
    #print(wb.get_sheet_names()[0])
    ws = wb.sheet_by_index(0)
    for row_index in range(1, ws.nrows): # Skip column headers
        mapnum = ws.cell(row_index, 0).value
        if mapnum:
            mo = re.search(regex, mapnum)
            if mo:
                cell = ws.cell(row_index, 1).value.strip()
                d_sortable[make_sortable(cell)] = cell
    
    return [d_sortable[k] for k in sorted(d_sortable)]

ret = re.compile(r'(\d*)(.*)')

def make_sortable(taxlotno):
    """ Given a taxlot number, reformat it into an ASCII sortable value. """
    sortable = ""
    mo = ret.search(taxlotno)
    if mo:
        n = mo.group(1)
        if not n: n = "0"
        s = mo.group(2)
        sortable = "%06d%s" % (int(n),s.strip())
    return sortable


def make_table(seq, columns):
    """ Break the sequence into 'n' columns and return them. """
    table = ""
    maxy = (len(seq)+columns-1)/columns
    i = 0
    columns = []
    for item in seq:
        table += str(item).ljust(6) + "\n"
        i += 1
        if not i % maxy:
            columns.append(table)
            table = ""
    if table:
        columns.append(table)

    return maxy,columns

def make_text_table(seq, columns):    
    """ Return a text string with a table in it, with the values
    sorted vertically into "columns" # of columns. """
    table = ''
    col_height = (len(seq)+columns-1) / columns
    l = 0
    # Calc column width by finding the longest string in input
    for x in seq:
        l = max(len(str(x)), l)
    l += 2
    for x in xrange(col_height):
        for col in xrange(columns):
            try:
                num = seq[x + (col_height * col)]
                table += str(num).ljust(l)
            except IndexError:
                pass
        table += '\n'
    return table

def test_make_table():
    maxc = 5
    maxy,columns = make_table([1,2,3,4,5,6,7,8,9,10,11,12,13,14,15], maxc)
    for column in columns:
        print(column)

    maxy,columns = make_table([1,2,3,4, 5,6,7,8, 9,10,11,12, 1,2,3,4, 5,6,7,8, 9,10,11,12, 1,2,3,4, 5,6,7,8, 9,10,11,12, 1,2,3,4, 5,6,7,8, 9,10,11,12, ], maxc)
    print("max y=",maxy)
    for column in columns:
        print(column)

def test_reader(q):
    l_cancelled = read_cancelled("K:/taxmaped/Clatsop/towned/cancelled.xlsx", q)
    print(q,len(l_cancelled), l_cancelled)
    return l_cancelled

def test_sorter(l_cancelled):
    d_sortable = {}
    for item in l_cancelled:
        d_sortable[make_sortable(item)] = item

    l_sorted = [d_sortable[k] for k in sorted(d_sortable)]
    print(l_sorted)

    maxy,columns = make_table(l_sorted, 5)
    for column in columns:
        print(column)

def test_taxlot_sorting():
    test_sorter([ "WATER", "300", "600M1", "600M2", "6000", "700", "600", "8", "800", "ROAD", "601M1", "600K"])
    test_sorter(["101A", "1200", "2703", "501", "902", "503", "503", "503", "503"])
    
# =============================================================================
if __name__ == "__main__":
    # unit tests
    
    test_taxlot_sorting()
    test_make_table()

    lst = test_reader("8.10.8BB")
    print(lst)

    lst = test_reader("8.10.8*")
    print(lst)
    
    lst = test_reader("8.10.25*")
    print(lst)

# That's all!
