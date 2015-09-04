#!/usr/bin/python
#-*- coding: UTF-8 -*-
import sys
import os
import logging
logging.basicConfig(filename='tim.log', format='%(asctime)s | %(name)s | %(levelname)s | %(message)s', level=logging.DEBUG)

from db import FileDatabase
from gui2db import Gui2Db
from mainview import Main
from tkgraphics import gallery_creator
from tagview import TagView
import keybindings

if __name__ == "__main__":
    dbname = 'master.sqlite'
    if len(sys.argv) > 1:
        dbname = sys.argv[1]
    logging.debug('Database: %s', dbname)

    run_init = False
    if not os.path.exists(dbname):
        logging.debug('run init on %s', dbname)
        run_init = True
    db = FileDatabase(dbname)
    if run_init:
        db.initialize()
    mainview = Main('TIM - Tagged Image Manager')

    glue = Gui2Db(db, mainview, 
            gallery_creator(mainview.new_view))

    tags = db.list_tags()
    tview = TagView(mainview.sidebar, tags, "Tags")
    keybindings.bind('mainview', (mainview, glue), mainview.root.bind_all)
    buttons = {
            'Add collection': glue.add_collection,
            'Remove collection': glue.remove_collection,
            'Remove deleted': glue.remove_deleted_files,
    }
    for label in buttons:
        mainview.add_menubutton(label, buttons[label])

    # Custom virtual events do not need to be user bindable
    # since their generation is user bindable. -> no dictionaries used.
    mainview.root.bind_all('<<TagViewSearch>>', glue.search_event)
    mainview.root.bind_all('<<TagViewEdit>>',
            lambda e: mainview.text_query('Edit tag:', e.widget.view.selection()[0]))
    mainview.root.bind_all('<<MainQueryAccept>>', glue.add_or_rename_tags)
    mainview.root.bind_all('<<GallerySelectionChanged>>', glue.update_selection_tags)
    mainview.root.bind_all('<<SlideShowNext>>', glue.update_selection_tags)
    mainview.root.bind_all('<<SlideShowPrev>>', glue.update_selection_tags)
    mainview.root.bind_all('<<MainViewChanged>>', glue.update_selection_tags)
    mainview.root.bind_all('<<NameViewSearch>>', glue.search_collection)

    mainview.add_sidebar(tview, 'main_tags')
    mainview.display()

