#!/usr/bin/python
#-*- coding: UTF-8 -*-

import gzip
import os
import sys
import subprocess
import xml.etree.ElementTree as ET

tmp = "tmp.xml"
app = "vim"

def parse(name, open_func):
    """Opens a collection file and returns its contents"""
    f = open_func(name)
    data = ET.parse(f)
    return data

def write(name, data, open_func):
    """Writes contents of data into a file called name."""
    f = open_func(name, 'w')
    data.write(f)
    
def open_in_app(name, app):
    """Opens file called name in app
    waits for user input before returning"""
    i = subprocess.call([app, name])

if __name__ == "__main__":
    
    name = sys.argv[1]
    data = parse(name, gzip.open)

    write(tmp, data, open)
    open_in_app(tmp, app)
    data = parse(tmp, open)
    write(name, data, gzip.open)
    os.remove(tmp)
