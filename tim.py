#!/usr/bin/python
#-*- coding: UTF-8 -*-
import sys
import os
import logging
logging.basicConfig(filename='tim.log', format='%(asctime)s | %(name)s | %(levelname)s | %(message)s', level=logging.DEBUG)

from db import FileDatabase
from gui2db import Gui2Db
from mainview import Main
from tkgraphics import gallery_with_slideshow
from tagview import TagView
from helpview import HelpView

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

    glue = Gui2Db(db, mainview)

    tags = db.list_tags()
    tview = TagView(mainview.sidebar, tags, "Tags")
    def jump_to_tag(tag, orig):
        tview.jump_to(tag)
        tview.widget.focus_set()

    actions = {
        'quit' : lambda e: mainview.quit(),
        'delete_view': mainview.delete_current_view,
        'add_tags' : lambda e: mainview.text_query('Add tags: '),
        'add_selected_tags': lambda e: glue.add_tags_from_tagview(e, tview),
        'add_images' : glue.add_files,
        'add_folder' : glue.add_directory,
        'remove_tags': glue.remove_tags_from_files,
        'jump_to_tag': lambda e: mainview.text_query('Jump to tag: ',
            accept_func=jump_to_tag),
        'focus_sidebar': lambda e: mainview.focus_sidebar(),
        'focus_main_view': lambda e: mainview.focus_main_view(),
        'toggle_selection_tags': glue.toggle_selection_tags,
        'toggle_collections': glue.toggle_collections,
        'tagstring_search': glue.search_tagstring,
        'help': lambda e: mainview.new_view(HelpView(mainview.root)),
        'add_to_collections': glue.add_to_collections,
    }
    keybindings.make_bindings(keybindings.appwide, actions, mainview.root.bind_all)
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
            lambda e: mainview.text_query('Edit tag:', tview.selection()[0]))
    mainview.root.bind_all('<<MainQueryAccept>>', glue.add_or_rename_tags)
    mainview.root.bind_all('<<GallerySelectionChanged>>', glue.update_selection_tags)
    mainview.root.bind_all('<<SlideShowNext>>', glue.update_selection_tags)
    mainview.root.bind_all('<<SlideShowPrev>>', glue.update_selection_tags)
    mainview.root.bind_all('<<MainViewChanged>>', glue.update_selection_tags)
    mainview.root.bind_all('<<NameViewSearch>>', glue.search_collection)

    mainview.add_sidebar(tview, 'main_tags')
    mainview.display()

