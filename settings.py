__author__  = "Tachara (tortured.flame@gmail.com)"
import xml.etree.ElementTree as ET
import os

class Settings():
    """Reads settings from an xml file.
    Part of cicm.
    """

    def __init__(self, settingsFile, open_func = None):
        self._file = settingsFile
        self.values = dict()
        self.tree = ET.ElementTree()
        if open_func != None:
            settingsFile = open_func(settingsFile)

        if open_func != None or os.path.exists(settingsFile):
            self.tree.parse(settingsFile)
        else:
            print "file: " + self._file + " could not be opened"
            return
        self._readSettings()
        self._correctTypes(self.values)

    def _readElem(self, elem):
        if len(elem) == 0:
            return elem.text

        data = dict()
        for subelem in elem:
            data[subelem.tag] = self._readElem(subelem)

        return data

    def _readSettings(self):
        root = self.tree.getroot()
        for elem in root:
            key = elem.tag
            if key in self.values.keys():
                print "A value for %s already exists.\
                        Check %s and remove the wrong one" % (key, self._file)
                self.values = dict()
                return
            self.values[key] = self._readElem(elem)

    def _convertType(self, item):
        if item.isdigit():
            return int(item)
        elif item.lower() == "true":
            return True
        elif item.lower() == "false":
            return False
        else:
            return item

    def _correctTypes(self, data):
        """changes the types of the 
        values to match the content of the
        string"""

        for key in data.keys():
            if isinstance(data[key], dict):
               self._correctTypes(data[key])
            else:
                data[key] = self._convertType(data[key])
    # end correctTypes

    def keys(self):
        return self.values.keys()

    def __getitem__(self, name):
        return self.values[name]
    
    def __setitem__(self, name, newValue):
        if isinstance(newValue, type(self.values[name])):
            self.values[name] = newValue
        else:
            self.values[name] = self._convertType(newValue)

    def write(self):
        root = self.tree.getroot()
        for elem in root:
            if len(elem) > 0:
                for subelem in elem:
                    subelem.text = str(self.values[elem.tag][subelem.tag])
            else:
                 elem.text = str(self.values[elem.tag])

        self.tree.write(self._file, encoding="UTF-8")

class Text(Settings):
    """Used for the texts. 
    Yes I (now) know there is a
    translation support(or whatever it's called)
    in python but I like this one"""
    
    def __init__(self, lang, filePath):
        fileName = "cicm_" + lang + ".xml"
        fullName = os.path.join(filePath, fileName)
        Settings.__init__(self, fullName)
