from helpview import HelpView

def jump_to_tag(mainview, tag, orig):
    tview = mainview.get_sidebar_view('main_tags')
    tview.jump_to(tag)
    tview.widget.focus_set()

__ = {
    'mainview': lambda mainview, glue: {
        'quit' : lambda e: mainview.quit(),
        'delete_view': mainview.delete_current_view,
        'add_tags' : lambda e: mainview.text_query('Add tags: ',
            complete_list=mainview.get_sidebar_view('main_tags').get_names()),
        'add_selected_tags': lambda e: glue.add_tags_from_tagview(e,
                    mainview.get_sidebar_view('main_tags')),
        'add_images' : glue.add_files,
        'add_folder' : glue.add_directory,
        'remove_tags': glue.remove_tags_from_files,
        'jump_to_tag': lambda e: mainview.text_query('Jump to tag: ',
            accept_func=lambda t, o: jump_to_tag(mainview, t, o),
            complete_list=mainview.get_sidebar_view('main_tags').get_names()),
        'focus_sidebar': lambda e: mainview.focus_sidebar(),
        'focus_main_view': lambda e: mainview.focus_main_view(),
        'toggle_selection_tags': glue.toggle_selection_tags,
        'toggle_collections': glue.toggle_collections,
        'tagstring_search': glue.search_tagstring,
        'help': lambda e: mainview.new_view(HelpView(mainview.root)),
        'add_to_collections': glue.add_to_collections,
        'export_collections': glue.export_collections,
        'import_collections': glue.import_collections,
    },
    'nameview' : lambda nameview: {
        'edit': lambda e: nameview.edit(),
        'search': lambda e: nameview.search(),
        'focus_next': lambda e: nameview.focus_next(),
        'focus_prev': lambda e: nameview.focus_prev(),
        'select': lambda e: nameview.select(),
        'clear_selection': lambda e: nameview.select(),
    },
    'gallery' : lambda gallery: { 
        'slide': gallery.activate,
        'clear_selection': lambda e: gallery.clear_selection(),
        'toggle_selection': gallery.toggle_selection,
        'cursor_up':gallery.cursor_up,
        'cursor_right':gallery.cursor_right,
        'cursor_left':gallery.cursor_left,
        'cursor_down':gallery.cursor_down,
        'load_more':lambda e: gallery.continue_loading()
    },
    'slideshow' : lambda slide: {
        'next':lambda e: slide.next(),
        'prev':lambda e: slide.prev(),
        'reload':lambda e: slide.reload()
    },
    'text_query': lambda query: {
        'accept': query.accept,
        'cancel': query.cancel,
        'complete_item': query.accept_completion,
    },
}


def create_actions(name, objects): 
    return __[name](*objects)

