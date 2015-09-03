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
from helpview import HelpView

import keybindings

def bind_mainview(mainview, glue):
    mainview_actions = {
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
        'toggle_selection_tags': lambda e : glue.toggle_selection_tags(e, bind_nameview),
        'toggle_collections': lambda e: glue.toggle_collections(e, bind_nameview),
        'tagstring_search': glue.search_tagstring,
        'help': lambda e: mainview.new_view(HelpView(mainview.root)),
        'add_to_collections': glue.add_to_collections,
        'export_collections': glue.export_collections,
        'import_collections': glue.import_collections,
    }
    keybindings.make_bindings(keybindings.appwide, mainview_actions, mainview.bind_all)

def bind_nameview(nameview):
    nameview_actions = {
        'edit': lambda e: nameview.edit(),
        'search': lambda e: nameview.search(),
        'focus_next': lambda e: nameview.focus_next(),
        'focus_prev': lambda e: nameview.focus_prev(),
        'select': lambda e: nameview.select(),
        'clear_selection': lambda e: nameview.select(),
    }
    keybindings.make_bindings(keybindings.tagview, nameview_actions, nameview.bind)

def bind_gallery(gallery):
    gallery_actions = { 
        'slide': gallery.activate,
        'clear_selection': lambda e: gallery.clear_selection(),
        'toggle_selection': gallery.toggle_selection,
        'cursor_up':gallery.cursor_up,
        'cursor_right':gallery.cursor_right,
        'cursor_left':gallery.cursor_left,
        'cursor_down':gallery.cursor_down,
        'load_more':lambda e: gallery.continue_loading()
    }
    keybindings.make_bindings(keybindings.gallery, gallery_actions, gallery.bind)

def bind_slideshow(slide):
    slide_actions= {
        'next':lambda e: slide.next(),
        'prev':lambda e: slide.prev(),
        'reload':lambda e: slide.reload()
    }
    keybindings.make_bindings(keybindings.slideshow, slide_actions, slide.bind)

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
            gallery_creator(mainview.new_view, bind_gallery, bind_slideshow))

    tags = db.list_tags()
    tview = TagView(mainview.sidebar, tags, "Tags")
    def jump_to_tag(tag, orig):
        tview.jump_to(tag)
        tview.widget.focus_set()

    bind_mainview(mainview, glue)
    bind_nameview(tview)
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

