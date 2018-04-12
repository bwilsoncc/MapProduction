# ORMAP - Map Production Tools

This is a set of tools built for ESRI ArcGIS Desktop 10.6 to support
the mapping requirments set forth by the Oregon Department of Revenue
for mapping tax parcels.

The tools are included in a Python Toolbox for access direct from an
ArcMap document.

There is also a lot of code here to perform the data conversion from
the original coverage data. It works in conjunction with the AML code
found in the bwilsoncc/DataConversion repo, also on github.

### Documentation/Configuration

The toolbox relies heavily on Data Driven Pages and has only a minimal
config file. Instead it reads settings from the MXD file and the DDP
index feature class.

The main component of this project is a "python toolbox" that contains
three tools

1. ZoomToMapNumber
2. PrintMaps

They are designed to be run only from inside an open MXD Map Document.

A separate Word format document is included in this repository with
more information on configuring and using this toolbox.

### Toolbox

Toolbox directory contains the Python Toolbox.
Nested inside it is a Python module "ormap" that is used by the toolbox
and by the conversion code.

### Conversion

These are the main files in the conversion process.

conversion.py - main program, calls the others
coverage_to_anno.py - conversion of annotation coverages to anno feature classes
coverage_to_geodatabase.py - conversion of coverages to feature classes
preprocess.py - code to drive the AML scripts to import coverages

For unit testing / development each py file has the ability to run standalone

I use Microsoft Visual Studio 2017 Community Edition to code and run everything.

There are other supporting files in the repo not listed here.
This includes VS project files, projection files, sample AML, *.CAL files...
