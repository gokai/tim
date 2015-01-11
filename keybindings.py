# CICM tkinter GUI keybingings
# Use tkinter keysequence syntax
# for example: '<Control-a>' means holding
# down control and pressing a.
# 'a' means pressing a on its own
# and 'as' means first pressing a then s.


# Thumbnail view bindings
gallery = {
        '<space>':'slide',
        'j':'cursor_down',
        'k':'cursor_up',
        'h':'cursor_left',
        'l':'cursor_right',
        '<Down>':'cursor_down',
        '<Up>':'cursor_up',
        '<Left>':'cursor_left',
        '<Right>':'cursor_right',
        '<Control-c>':'clear_selection',
        '<Return>':'slide'
}

# Full view bindings
slideshow = {
        'n':'next',
        'p':'prev',
        'r':'reload'
}

# Bindings global to the application
appwide = {
        '<Control-q>':'quit',
        '<Control-w>':'next_view',
        '<Control-d>':'delete_view',
        '<Control-a>':'add_tags',
        '<Control-o>':'add_images',
        '<Control-p>':'add_folder',
        '<Control-t>':'remove_tags',
}

# Bindings for the tagview on the sidebar
tagview = {
        'e':'edit',
        's':'search',
        '<space>':'select',
        'j':'focus_next',
        'k':'focus_prev',
        '<Return>':'search',
        '<Up>':'focus_prev',
        '<Down>':'focus_next',
}

# Bindings for text entries
text_query = {
        '<Return>':'accept',
        '<Escape>':'cancel'
}


def make_bindings(bindings, actions, bind_func):
    """Creates bindings defined in bindings with bind_func.
       bindings   dict as above
       actions    dict with action name as key and callback as value
       bind_func  tk.widget.bind or tk.widget.bind_all"""
    for key in bindings.keys():
        try:
            bind_func(key, actions[bindings[key]])
        except KeyError:
            print('Invalid action: ', bindings[key])