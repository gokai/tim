
from configparser import ConfigParser
import os
import logging
logger = logging.getLogger(__name__)

from tkinter import ttk

class Theme(object):

    defaults = {
            'bg': 'black', 'fg': '#aa00aa',
            'focusfg': 'orange', 'focusbg': 'black',
            'hlcolor': 'red', 'scrollbg': '#330033'}

    def __init__(self, filename=None):
        self.parser = ConfigParser()
        self.filename = filename
        if (filename is not None):
            self.parser.read(filename)

    def open(self, filename):
        if not os.path.exists(filename):
            return

        self.parser.read(filename)

    def write(self):
        name = self.filename
        if name is None:
            name = 'cicm_theme.ini'
        with open(name, 'w') as configfile:
            self.parser.write(configfile)


    def get(self, key, default=None):
        if default is None:
            default = self.defaults.get(key, None)
        val = self.parser['theme'].get(key, fallback=default)
        return val

    def apply_theme(self, name='.'):
        """ Apply the theme on top of an existing TK style.
        name    Name of the TK style to apply to. Default '.'
        """
        s = ttk.Style()
        s.configure(name,
            background = self.get('bg'),
            foreground = self.get('fg'),
            troughcolor = self.get('scrollbg'),
            relief = 'groove',
            borderwidth = 0,
        )
        s.configure("TButton", borderwidth = 1)
        s.map(name,
            foreground = [('focus', self.get('hlcolor')),
                ('selected', self.get('focusfg')),
                ('active', self.get('hlcolor'))],
            background = [('focus', self.get('focusbg')),
                ('selected', self.get('focusbg')),
                ('active', self.get('focusbg'))
                ],
            highlightcolor = [('focus', self.get('hlcolor'))],
        )
