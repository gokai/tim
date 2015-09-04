# CICM tkinter GUI keybingings
# Use tkinter keysequence syntax
# for example: '<Control-a>' means holding
# down control and pressing a.
# 'a' means pressing a on its own
# and 'as' means first pressing a then s.

from configparser import ConfigParser
import logging
logger = logging.getLogger(__name__)

import actions

config = ConfigParser()
config.optionxform = lambda option: option
config.read('keys.ini')

def make_bindings(bindings, ac, bind_func):
    """Creates bindings defined in bindings with bind_func.
       bindings   dict as above
       actions    dict with action name as key and callback as value
       bind_func  tk.widget.bind or tk.widget.bind_all"""
    for key in bindings.keys():
        try:
            bind_func(key, ac[bindings[key]])
        except KeyError:
            logger.warning('Invalid action %s', key)

def bind(name, objects, bind_func):
    ac = actions.create_actions(name, objects)
    make_bindings(config[name], ac, bind_func)

