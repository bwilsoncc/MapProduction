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
    print(regex)
    lst = []
    wb = xlrd.open_workbook(xlfile)
    #print(wb.get_sheet_names()[0])
    ws = wb.sheet_by_index(0)
    for row_index in range(1, ws.nrows): # Skip column headers
        mapnum = ws.cell(row_index, 0).value
        if mapnum:
            mo = re.search(regex, mapnum)
            if mo:
                lst.append(ws.cell(row_index, 1).value)
    return lst

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

def test_taxlot_sorting():
    ltl = [ "WATER", "300", "600M1", "600M2", "6000", "700", "600", "8", "800", "ROAD", "601M1", "600K"]
    ltl = ["101A", "1200", "2703", "501", "902", "503"]
    stl = []
    for tl in ltl:
        stl.append((make_sortable(tl), tl))
    for tl in sorted(stl):
        print("%s" % tl[1])

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
    maxy,columns = make_table([1,2,3,4, 5,6,7,8, 9,10,11,12], 4)
    for column in columns:
        print(column)

    maxy,columns = make_table([1,2,3,4, 5,6,7,8, 9,10,11,12, 1,2,3,4, 5,6,7,8, 9,10,11,12, 1,2,3,4, 5,6,7,8, 9,10,11,12, 1,2,3,4, 5,6,7,8, 9,10,11,12, ], 4)
    print("max y=",maxy)
    for column in columns:
        print(column)

def test_reader(q):
    l_cancelled = read_cancelled("K:/taxmaped/Clatsop/towned/cancelled.xlsx", q)
    print(q,len(l_cancelled), l_cancelled)
    return l_cancelled

def test_sorter(l_cancelled):
    print("Cancelled accounts")    
    l_sortable = []
    for item in l_cancelled:
        l_sortable.append((make_sortable(item), item))

    l_sorted = []
    for tl in sorted(l_sortable):
        l_sorted.append(tl[1])
    #print(l_sorted)

    maxy,columns = make_table(l_sorted, 4)
    for column in columns:
        print(column)
    
# =============================================================================
if __name__ == "__main__":
    # unit tests
    
    test_make_table()
    #test_taxlot_sorting()
    #lst = test_reader("8.10.8")
    #lst = test_reader("8.10.8*")
    #lst = test_reader("8.10.25*")
    #test_sorter(lst)
    
# That's all!
