#!/bin/env python
# coding: utf-8

from cmd import Cmd

def parse_int_list(list_str, sep):
    str_list = list_str.split(sep)
    return [int(i) for i in str_list]

class HelpString:
    def __init__(self, s, stdout):
        self.s = s + "\n"
        self.stdout = stdout

    def __call__(self):
        self.stdout.write(self.s)

class CommandInterpreter(Cmd):

    def __init__(self):
        Cmd.__init__(self)
        self.prompt = "> "
        self.intro = "Welcome to the CommandInterpreter"
        self.ruler = '-'

    def do_quit(self, arg_str):
        """Exits the program"""
        return True

    def default(self, line):
        self.stdout.write("%s not found\n" % line.split()[0])

    def do_help(self, arg_str):
        attrs = dir(self)
        self.stdout.write("\n" + self.doc_header + "\n")
        for attr in attrs:
            if attr.startswith("do_"):
                name = attr[3:]
                func = False
                doc = False
                try:
                    func = getattr(self, "help_" + name)
                except AttributeError:
                    doc = getattr(self, attr).__doc__

                self.stdout.write("\t" + name + "\t" )
                if func:
                    func()
                elif doc:
                    self.stdout.write(doc)
                self.stdout.write("\n")
                    

    def get_names(self):
        """Override base classes method to return instances
           attributes instead of class attributes"""
        return dir(self)

    def emptyline(self):
        pass
    
    def help_help(self):
        self.stdout.write("Prints help abput a topic")

    def add_command(self, name, handler, help_str):
        setattr(self, "do_" + name, handler)
        setattr(self, "help_" + name, HelpString(help_str, self.stdout))
