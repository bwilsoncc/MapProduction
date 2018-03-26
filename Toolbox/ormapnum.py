# -*- coding: utf-8 -*-
"""
A class for managing ORMAPNUMs

Created on Thu Dec 14 11:16:07 2017
@author: Brian Wilson
"""
from __future__ import print_function
import struct
from mapnum import mapnum

# dict to translate part to fraction
d_partfrac = {
         None:"",
        '.00':"",
        '.25':"1/4",
        '.50':"1/2",
        '.75':"3/4",
        }

class ormapnum(object):

    county          = 4     # County as a number, 1 to 34 or something.
    township        = 0
    township_part   = '.00'   # 0 or 25 or 50 or 75
    township_dir    = "N"   # {N|S}
    range           = 0
    range_part      = '.00'
    range_dir       = "W"   # {E|W}
    section         = 0     # 01-31
    quarter         = "0"   # {0|A|B|C|D}
    quarterquarter  = "0"   # {0|A|B|C|D}
    anomaly         = "--"  # ?? I wonder what this is for ??
    mapsuffixtype   = "0"   # {0 | D for Detail | S for Supplemental | T for Sheet}
    mapsuffixnumber = 0
    
    def __init__(self):
        self.township_frac = d_partfrac[self.township_part]
        self.range_frac = d_partfrac[self.range_part]
        return
    
    def __str__(self):
        """ Return a packed 24 character ormap string. """
        return self.ormapnumber

    @property
    def ormapnumber(self):
        """ Put all the properties into a standard ORMAP string. """
        
        dst = self.mapsuffixtype
        if not dst: dst = '0'

        p = "%02d" + \
            "%02d%3s%s" + \
            "%02d%3s%s" + \
            "%02d" + \
            "%s%s" + \
            "%s" + \
            "%s%03d"

        return p % (
                self.county, 
                self.township, self.township_part, self.township_dir, 
                self.range,    self.range_part,    self.range_dir,
                self.section,
                self.quarter, self.quarterquarter,
                self.anomaly,
                self.mapsuffixtype, self.mapsuffixnumber
                )
    
    
    def qq(self):
        s = ""
        if self.quarter != '0':
            s = self.quarter
            if self.quarterquarter != '0':
                s += self.quarterquarter
        return s
    
    def qqtext(self):
        """ Convert quarter,quarterquarter in letter format (0ABCD) to human readable text. """
        
        d_qtr = {
                '0' : '',
                'A' : "NE 1/4",
                'B' : "NW 1/4", 
                'C' : "SW 1/4",
                'D' : "SE 1/4"
                }

        if self.quarter == '0':
            s = ''
        elif self.quarterquarter != '0':
            s = d_qtr[self.quarterquarter] + " " + d_qtr[self.quarter]
        else:
            s = d_qtr[self.quarter] 
            
        return s

    def shortmaptitle(self):
        """ Return text string usable for short title.
        Example: 8 08 01 AA """
    
        smt = '%d %02d' % (self.township, self.range)
        if self.section>0: smt += " %02d" % self.section

        # possibly add the letters like 'AA'
        if self.quarter != '0':
            smt += ' ' + self.quarter
            if self.quarterquarter != '0':
                smt += self.quarterquarter

        return smt

    def longmaptitle(self):
        """ Return text string usable for long titles.
        Example: SE 1/4 SE 1/3 SEC.16 T8N R10W WM """
    
        townrng = "T" + str(self.township) + self.township_frac + self.township_dir + ' ' + \
                  "R" + str(self.range)    + self.range_frac    + self.range_dir    + " WM"

        lmt = townrng
        if str(self.section):
            qqtext = self.qqtext()
            if qqtext:
                l1 = qqtext + " SEC." + str(self.section)
            else:
                l1 = "SECTION " + str(self.section)   

            lmt = l1 + ' ' + townrng
            try:
                # If there is a "map suffix" then split the title on 2 lines.
                s_sfx = {'D':'DETAIL', 'S':'SUPPLEMENTAL', 'T':'DETAIL'}[self.mapsuffixtype]
                lmt = l1 + '\n' + townrng + " %s %d" % (s_sfx, self.mapsuffixnumber)
            except KeyError:
                pass

        return lmt
    
    def shorten(self):
        """ Return a shortened format that's easier to read and sort. """
       
        shortie = "%d %02d" % (self.township, self.range)
        
        section = self.section
        if section > 0: 
            shortie += " %d" % section

        shortie += self.qq()

        if self.mapsuffixtype != '0':
            shortie += " %s%s" % (self.mapsuffixtype,self.mapsuffixnumber)
        return shortie

    def expand(self, shortie):
        """ Unpack a shortened string like "8.10.5CD D001 into properties. """
        mn = mapnum(shortie)
        self.county         = 4
        self.township       = int(mn.t)
        self.range          = int(mn.r)
        self.section        = int(mn.s)
        self.quarter        = "0"
        self.quarterquarter = "0"
        if len(mn.q)>0:
            self.quarter = mn.q[0]
            if len(mn.q)>1:
                self.quarterquarter = mn.q[1]
        if len(mn.suffix)>0:
            self.mapsuffixtype = mn.suffix[0]
            self.mapsuffixnumber = int(mn.suffix[1:])
        else:
            self.mapsuffixtype = '0'
            self.mapsuffixnumber = 0
            
        return self.ormapnumber
        
    def unpack(self, s):
        """ Unpack a 23- or 24-character "ORTAXLOT" string into separate properties. """
        
        # The AML code erroneously fails to zero fill township,
        # and sometimes it puts an extra zero in range, 
        # so watch for both of these errors and fix them here.

        # county
        u = "2s"

        # township
        # # township in Clatsop ALWAYS has a leading zero, range is 4...9
        if s[2] != '0':
            # This case should never happen again; I fixed the AML 2/26/18
            u += "1s"  # handle missing leading zero
            rdot = 10
        else:
            u += "2s"  # normal 2 digit township
            rdot = 11

        # township part {.00|.25|.50|.75}
        # township dir 
        u += "3sc"

        if s[rdot] == '.':
            # section should be 2 digits with zero fill but our broken AML 
            # used to put in an extra zero -- fixed now I think
            u += "3s" # absorb extra leading zero
        else:
            u += "2s"

        u += "3sc2scc2sc3s"

        try:
            t = struct.unpack(u, s)
        except Exception as e:
            print("Unpack('%s') %s : %s" % (s,len(s),e))
            return
            
        self.county          = int(t[0])
        self.township        = int(t[1])
        self.township_part   = t[2]
        self.township_dir    = 'N'          # FORCE to N no matter what AML code does!!! t[3]
        self.range           = int(t[4])
        self.range_part      = t[5]
        self.range_dir       = 'W'          # FORCE to W no matter what AML code does!!! t[6]
        self.section         = int(t[7])
        self.quarter         = t[8]
        self.quarterquarter  = t[9]
        self.anomaly         = t[10]
        self.mapsuffixtype   = t[11]
        self.mapsuffixnumber = int(t[12])
        #print(t)
        self.township_frac   = d_partfrac[self.township_part]
        self.range_frac      = d_partfrac[self.range_part]
            
        # if I were going to do bounds checks, here would be a good place for them.

        # This is Clatsop county based
        if self.township < 4 or self.township > 9:
            raise ValueError("Township(%s) of out expected range." % self.township)
        if self.range < 6 or self.range > 11:
            raise ValueError("Range(%s) of out expected range." % self.range)
        if self.section < 0 or self.section > 36: # section = 0 means section is not set and that's okay
            raise ValueError("Section(%s) of out expected range." % self.section)

        return

# ---------------------------------------
    
if __name__ == "__main__":
# Unit test

    orm = ormapnum()
    
    # Test the handling of Q and QQ strings
    lq = ['0', 'A', 'B', 'C', 'D']
    for q in lq:
        for qq in lq:
            orm.quarter = q
            orm.quarterquarter = qq
            print(q, qq, " => ", orm.qq(), '\t', orm.qqtext())
            
    # Test unpacking            
    # Test expanding a shortie
    samples = [
                u'048.00N10.00W0000--0000',   # Dropped zero in TOWN, handle this please
                u'048.00N09.00W0000--0000',   # Dropped zero in TOWN, handle this please
                u'048.00N009.00W0000--0000',   # Dropped zero in TOWN, handle this please

                u'0408.00N10.00W0000--0000',
                u'0408.00N10.00W25AD--D001',
                u'0409.00N10.00W0000--0000',
                u'0408.00N10.00W25AD--0000',
                ]
    for sample in samples:
        orm.unpack(sample)
        ormapnum = orm.ormapnumber
        if ormapnum != sample: 
            print(" assert pack fail \"%s\" != \"%s\"" % (sample, ormapnum))
        print(ormapnum, len(ormapnum))
        shortie = orm.shorten()
        print("shortened", shortie)
        expanded = orm.expand(shortie) 
        print("expanded", expanded, len(expanded))
        if sample != expanded: 
            print(" assert expand failed \"%s\" != \"%s\"" % (sample, expanded))
        print()
        #orm.ormapnumber()
        #print(mapnum)

        print("short title: \"%s\"" % orm.shortmaptitle())
        print("long title: \"%s\"" % orm.longmaptitle())
    