# -*- coding: utf-8 -*-
"""
Created on Wed Dec 27 12:09:30 2017

@author: bwilson
"""
from __future__ import print_function
import re

# =============================================================================
class mapnum(object):
    """ Facilitates processing map numbers, 
        notably by sorting them correctly. """

    def __init__(self, m):
        self.__t = self.__r = self.__s = 0
        self.__q = ""
        self.__mapsuffix = ""
        try:
            mo = re.match(r'(\d+)\.(\d+)(\.(\d+)([A-D]?[A-D]?))?(\s([DST]?\d+))?', m.upper())
            self.__t = int(mo.group(1))
            self.__r = int(mo.group(2))
            if mo.group(4):
                self.__s = int(mo.group(4))
            if mo.group(5):
                self.__q = mo.group(5)
            if mo.group(7):
                self.__mapsuffix = mo.group(7)
        except Exception as e:
            print("mapnum(%s) %s" % (m,e))
        return
    
    @property
    def t(self):
        return str(self.__t)

    @property
    def r(self):
        return str(self.__r)

    @property
    def s(self):
        return str(self.__s)
    
    @property
    def q(self):
        return self.__q

    @property
    def suffix(self):
        return self.__mapsuffix
    
    @property
    def number(self):
        """ Return TRSQ as a long number, useful for sorting lists. """
        s = self.__s
        if not s: s = 0
        
        # Convert QQ from letters like AA into a number from 00 to 44
        q = qq = 0
        if len(self.__q) >= 1:
            q = ord(self.__q[0]) - (ord("A")-1)
            if len(self.__q) > 1:
                qq = ord(self.__q[1]) - (ord("A")-1)
        sfx = 0
        if self.__mapsuffix:
            dtyp = {'D':1000, 'S':2000, 'T':3000}
            sfx = dtyp[self.__mapsuffix[0]] + int(self.__mapsuffix[1:]) 

        return int("%2d%02d%02d%d%d%04d" % (self.__t, self.__r, s, q, qq, sfx))
    
    def __str__(self):
        if self.__s > 0:
            rval = "%s.%s.%s%s" % (self.t, self.r, self.s, self.q)
        else:
            rval = "%s.%s" % (self.t, self.r)
        if self.__mapsuffix:
            rval += ' ' + self.__mapsuffix
        return rval

# =============================================================================
if __name__ == "__main__":
    # unit tests
    
    tests = ["8.10", "8.10 D1", "8.10.20 D2", "8.10.20A T1", "10.10.1AB T2",
             "8.10.25", "5.10.25ab", "5.2.23", "10.7.10bcd"]
    tested = []
    
    print("test")
    for t in tests:
        mn = mapnum(t)
        tested.append(mn)
        print(t, ":", mn)
                
    print("results")
    for t in sorted(tested, key=lambda mapnum:mapnum.number):
        print(t)
    pass

# That's all!

