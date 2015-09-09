#!/bin/python

# Creates a gzipped tar package of the procjects source files.

import tarfile
import time
import sys

files = (
    "tim.py",
    "mainview.py",
    "tkgraphics.py",
    "db.py",
    "tagview.py", 
    "gui2db.py",
    "keybindings.py",
    "helpview.py",
    "dialog.py",
    "query.py",
    "actions.py",
    "keys.ini",
    "README.md",
    "UNLICENSE",
)

# Format for time.strftime which returns a string of the date
# based on the format.
# %d - Day as decimal
# %m - Month as decimal
# %Y - Full year as decimal
filename_format = "tim-%Y%m%d.tar.gz"
filename =  time.strftime(filename_format)
if len(sys.argv) > 1:
    filename = sys.argv[1]

with tarfile.open(name=filename, mode="w:gz") as package:
    for fi in files:
        package.add(fi)

