#!/bin/python

import tarfile
import time
import sys

files = (
    "cicm.py",
    "tkgui.py",
    "tkgraphics.py",
    "db.py",
    "tagview.py", 
    "gui2db.py",
    "keybindings.py",
    "helpview.py",
    "dialog.py",
)

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

