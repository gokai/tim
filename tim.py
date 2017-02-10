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
import theme

if __name__ == "__main__":
    dbname = 'master.sqlite'
    if len(sys.argv) > 1:
        dbname = sys.argv[1]
    logging.debug('Database: %s', dbname)

    db = FileDatabase(dbname)
    mainview = Main('TIM - Tagged Image Manager')

    apptheme = theme.Theme('theme.ini')
    mainview.set_theme(apptheme)
    # need to apply theme a bit everywhere to get consistent look
    apptheme.apply_theme()
    apptheme.apply_theme('Treeview')
    apptheme.apply_theme('TNotebook.Tab')

    glue = Gui2Db(db, mainview, apptheme, 
            gallery_creator(mainview.new_view, apptheme))

    tags = db.list_tags()
    names, counts = list(), list()
    for t in sorted(tags, key=lambda s: s['name']):
        names.append(t['name'])
        counts.append(t['file_count'])
    tview = TagView(mainview.sidebar, names, apptheme, "Tags", counts)
    keybindings.bind('mainview', (mainview, glue), mainview.root.bind_all)
    buttons = {
            'Add collection': glue.add_collection,
            'Remove collection': glue.remove_collection,
            'Remove deleted': glue.remove_deleted_files,
    }
    for label in buttons:
        mainview.add_menubutton(label, buttons[label])

    def view_changed(event):
        glue.update_selection_tags(event)
        apptheme.apply_theme('TNotebook.Tab')
    # Custom virtual events do not need to be user bindable
    # since their generation is user bindable. -> no dictionaries used.
    mainview.root.bind_all('<<TagViewSearch>>', glue.search_event)
    mainview.root.bind_all('<<TagViewEdit>>',
            lambda e: mainview.text_query('Edit tag:', e.widget.view.selection()[0]))
    mainview.root.bind_all('<<MainQueryAccept>>', glue.add_or_rename_tags)
    mainview.root.bind_all('<<GallerySelectionChanged>>', glue.update_selection_tags)
    mainview.root.bind_all('<<SlideShowNext>>', glue.update_selection_tags)
    mainview.root.bind_all('<<SlideShowPrev>>', glue.update_selection_tags)
    mainview.root.bind_all('<<MainViewChanged>>', view_changed)
    mainview.root.bind_all('<<NameViewSearch>>', glue.search_collection)
    mainview.root.bind_all('<<NameViewEdit>>', glue.edit_collection)
    mainview.root.bind_all('<<CollectionEditClose>>', lambda e: mainview.remove_sidebar_view('collection_edit'))

    mainview.add_sidebar(tview, 'main_tags')
    mainview.display()

