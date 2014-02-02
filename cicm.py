#!/usr/bin/python
#-*- coding: UTF-8 -*-

"""cicm - Console Image Collection Manager
Cicm is a free software that creates, edits
and manages image collections. It's also a
sample ui for xfclib. See readme.txt
for usage guide"""

__author__  = "Tachara (tortured.flame@gmail.com)"
__date__ = "$Date 2010/31/03 18:07:00 $"
__copyright__ = "Copyright (c) 2010 Tachara"

import sys
import os

from ui import get_file_dir, ImageView
from cui import CicmInterpreter, ImageCollectionLibrary
from settings import Settings, Text
__found_gui = True
try:
    from gui import GUI
except ImportError as ie:
    __found_gui = False

if __name__ == "__main__":
    
    cicmpath = get_file_dir()
    wd       = os.getcwd()
    os.chdir(cicmpath)

    settings = Settings("cicm.xml")
    args     = sys.argv
    argc     = len(args)

    command = ""
    if argc > 1:
        command = args[1]

    collspath = os.path.join(cicmpath, settings["colls"])
    if not os.path.exists(collspath):
        os.mkdir(collspath)
    if command != "graph":
        graphics    = ImageView()
        short_paths = Settings(os.path.join(cicmpath, settings["paths"]))
        lang        = Text(settings["lang"], cicmpath)
        library     = ImageCollectionLibrary(cicmpath, settings, short_paths, lang)
        interpreter = CicmInterpreter(wd, settings, graphics, library)
        interpreter.intro = "Welcome to cicm!"
        if command != "":
            interpreter.onecmd(" ".join(args[1:]))
        else:
            interpreter.cmdloop()
    elif __found_gui:
        gui = GUI()
        gui.main()
