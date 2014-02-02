#!/bin/python

import tarfile
import time
import sys

files = ("cicm.py", "ui.py", "cui.py", "gui.py", "interpreter.py",
         "xfclib/__init__.py", "xfclib/manager.py", "xfclib/collection.py",
         "colls/skeleton.xic.base", "settings.py", "cicm_en.xml", "cicm_fi.xml", "graphics.py", 
         "cicm.xml", "icon_gallery.svg", "icon_slide.svg")

# Format for time.strftime which returns a string of the date
# based on the format.
# %d - Day as decimal
# %m - Month as decimal
# %Y - Full year as decimal
filename_format = "cicm-%Y%m%d.tar.gz"
filename =  time.strftime(filename_format)
if len(sys.argv) > 1:
    filename = sys.argv[1]

with tarfile.open(name=filename, mode="w:gz") as package:
    for fi in files:
        package.add(fi)

