# ORMAP - Map Production Tools

This is a fork of the original tools, this version has been tailored
to support Clatsop County.

This is a set of tools built for ESRI ArcGIS Desktop (10.5.1/10.6 at the
moment) to support the mapping requirments set forth by the Oregon
Department of Revenue for mapping tax parcels. 

The tools are included in a Python Toolbox for access direct from an
ArcMap document.

There is probably only 1% of the original fork, the approach used here
is very different.

### Documentation/Configuration

The original project used an "add-in". This project uses a python toolbox.

The philosophy of the original version was to use an extensive set of
configuration files. It was designed without using Data Driven Pages.

This version relies heavily on Data Driven Pages and has only a minimal
config file. Instead it reads settings from the MXD file and the
DDP index feature class.

The main component of this project is a "python toolbox" that contains
three tools

1. ZoomToMapNumber
2. PrintMaps
3. MXDReport

They are all designed to be run from inside an open MXD Map Document.

A separate Word format document is included in this repository with
more information on configuring and using this toolbox.







