#
#  This is intended to be called from inside an AML script.
#  It fixes the ormapnum column in a coverage.
#
from __future__ import print_function
import os, sys
import logging
import arcpy
from Toolbox.ormapnum import ormapnum

def posttaxmap(fc):
    """ Code to run after stage 01.
    Fix taxbound ormapnum, the AML code to create ormapnum is broken for detail maps. """

    logging.info("post01(%s)" % fc)

    fields = ["ORMAPNUM", "PAGENAME", "MAPSUFNUM", "OID@"]
    ORMAPNUM  = 0
    PAGENAME  = 1
    MAPSUFNUM = 2
    OID       = 3

    orm = ormapnum()
    
    with arcpy.da.UpdateCursor(fc, fields) as cursor:
        for row in cursor:
            o   = row[ORMAPNUM]
            oid = row[OID]
            if not o:
                try:
                    # mysteriously, some ormapnumbers are just empty
                    cursor.deleteRow()
                    logging.debug("Deleted empty row.")
                except Exception as e:
                    logging.warn("Could not delete empty row(%s). %s" % (oid, e))
                continue

        # repair detail map number
            if o[-1] == 'D':
                o += "%03d" % row[MAPSUFNUM]
                orm.unpack(o)
                row[ORMAPNUM] = orm.ormapnumber 
                logging.info("Repaired %s" % row[ORMAPNUM])

            try:
                orm.unpack(o)
            except ValueError as e:
                logging.warn(e)

            if orm.township == 0 or orm.range == 0:
                try:
                    # mysteriously, some ormapnumbers are 0,0
                    cursor.deleteRow()
                    logging.debug("Deleted 0,0 row.")
                except Exception as e:
                    logging.warn("Could not delete 0,0 row(%s). %s" % (oid, e))
                continue

        # calc page number from ormapnum
            row[PAGENAME] = orm.short
            cursor.updateRow(row)
            pass
    return

if __name__ == "__main__":

    MYNAME  = os.path.splitext(os.path.split(__file__)[1])[0]
    LOGFILE = MYNAME + ".log"
    FORMAT = '%(asctime)s %(message)s'
    logging.basicConfig(filename=LOGFILE, level=logging.DEBUG, format=FORMAT)

    workfolder = sys.argv[1]
    fc = os.path.join(workfolder, sys.argv[2])

    posttaxmap(fc)


