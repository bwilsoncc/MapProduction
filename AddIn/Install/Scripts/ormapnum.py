# -*- coding: utf-8 -*-
"""
A class for managing ORMAPNUMs

Created on Thu Dec 14 11:16:07 2017
@author: Brian Wilson
"""
from __future__ import print_function
import struct

# dict to translate part to fraction
d_partfrac = {
        None:"",
        0.00:"",
        0.25:"1/4",
        0.50:"1/2",
        0.75:"3/4",
        }

class ormapnum(object):
    
    county         = 4     # County as a number, 1 to 34 or something.
    township       = "00"
    township_part  = .50   # 0 or 25 or 50 or 75
    township_dir   = "N"   # N or S
    range          = "00"
    range_part     = .00
    range_dir      = "E"   # E or W
    section        = 0     # 01-31
    quarter        = "0"   # 0 or A
    quarterquarter = "0"
    anomaly        = "--"  # ?? I wonder what this is for ??
    maptype        = "S"   # 0 or D for Detail or S for Supplemental or T for Sheet
    mapnumber      = 25
    
    def __init__(self):
        self.township_frac = d_partfrac[self.township_part]
        self.range_frac = d_partfrac[self.range_part]
        return
    
    def __str__(self):
        """ For now this is just me doing debugging so return a tuple with all the parts as a string. """
        return str((self.county, 
            self.township, self.township_part, self.township_frac, self.township_dir, 
            self.range, self.range_part, self.range_frac, self.range_dir,
            self.section,
            self.quarter, self.quarterquarter,
            self.anomaly,
            self.maptype, self.mapnumber
            ))

    def qqtext(self):
        """ Convert quarter,quarterquarter in letter format (0ABCD) to human readable text. """
        
        d_qtr = {
                '0' : '',
                'A' : "N.E.1/4",
                'B' : "N.W.1/4", 
                'C' : "S.W.1/4",
                'D' : "S.E.1/4"
                }

        if self.quarter == '0':
            s = ''
        elif self.quarterquarter != '0':
            s = d_qtr[self.quarterquarter] + " " + d_qtr[self.quarter]
        else:
            s = d_qtr[self.quarter] 
            
        return s
    
    def unpack(self, s):
        """ Unpack an "ORTAXLOT" string into separate attribute fields. """
        t = struct.unpack("2s2s3sc2s3sc2scc2sc3s", s)
        self.county = t[0]
        self.township = int(t[1])
        self.township_part = float(t[2])
        self.township_dir = t[3]
        self.range = t[4]
        self.range_part = float(t[5])
        self.range_dir= t[6]
        self.section = t[7]
        self.quarter = t[8]
        self.quarterquarter = t[9]
        self.anomaly = t[10]
        self.maptype = t[11]
        self.mapnumber = int(t[12])
        #print(t)
        
        self.township_frac = d_partfrac[self.township_part]
        self.range_frac    = d_partfrac[self.range_part]
            
        # if I were going to do bounds checks, here would be a good place for them.
        
        return
        
    def pack(self):
        """ Put all the attributes into a string. """
        raise BaseException("I have not written pack method yet.")
    
# ---------------------------------------
    
if __name__ == "__main__":
# Unit test

    mapnum = ormapnum()
    print(mapnum)
    
    lq = ['0', 'A', 'B', 'C', 'D']
    for q in lq:
        for qq in lq:
            mapnum.quarter = q
            mapnum.quarterquarter = qq
            print(q, qq, " => ", mapnum.qqtext())
            
    sample = u'0408.00N10.00W25AD--0000'
    
    mapnum.unpack(sample)
    print(mapnum)

    mapnum.pack()
    print(mapnum)
    