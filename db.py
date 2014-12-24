#!/usr/bin/python
# A simple database class to handle tagging files.

__license__ = "WTFPL"
__version__ = "alpha-0.1"

#TODO: return values?
#TODO: a fix for os.path.commonprefix

import sqlite3
import os
import datetime
import tarfile
import csv

SEARCH_EXCLUSIVE = 'e'
SEARCH_INCLUSIVE = 'i'

# CSV dialect used for exporting.
# using Unit and record separator chars as delimiters
# -> no collisions
class ExportDialect(csv.Dialect):
    delimiter = "\u001F"
    doublequote = False
    lineterminator = "\u001E"
    quoting = csv.QUOTE_NONE
    skipinitialspace = True
    strict = True


class FileDatabase(object):

    def __init__(self, dbname):
        """Connects to a database with the name dbname.
           dbname  name of the database file.
           If creating a new file call initialize afterwards.
        """
        self.connection = sqlite3.connect(dbname)
        self.connection.row_factory = sqlite3.Row
        cursor = self.connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        self.connection.commit()

    def initialize(self):
        """Creates the tables used into the database file."""
        cursor = self.connection.cursor()
        cursor.execute("BEGIN")
        cursor.execute("""CREATE TABLE paths(id INTEGER PRIMARY KEY,
                name TEXT NOT NULL UNIQUE ON CONFLICT IGNORE)""")
        cursor.execute("""CREATE TABLE files(id INTEGER PRIMARY KEY,
            name TEXT NOT NULL, path INTEGER NOT NULL, date INTEGER NOT NULL,
            FOREIGN KEY(path) REFERENCES paths(id)
            ON UPDATE CASCADE ON DELETE CASCADE)""")
        # If a tag is added with a name already in the database
        # -> IGNORE since the tag is already present.
        cursor.execute("""CREATE TABLE tags(id INTEGER PRIMARY KEY,
            name TEXT NOT NULL UNIQUE ON CONFLICT IGNORE)""")
        cursor.execute("""CREATE TABLE file_tags(
            file_id INTEGER NOT NULL, tag_id INTEGER NOT NULL,
            FOREIGN KEY(file_id) REFERENCES files(id) 
            ON DELETE CASCADE ON UPDATE CASCADE,
            FOREIGN KEY(tag_id) REFERENCES tags(id) 
            ON DELETE CASCADE ON UPDATE CASCADE)""")
        cursor.execute("""CREATE TABLE collections(
            id INTEGER PRIMARY KEY, 
            name TEXT NOT NULL UNIQUE ON CONFLICT IGNORE)""")
        cursor.execute("""CREATE TABLE collection_tags(
            collection_id INTEGER NOT NULL, tag_id INTEGER NOT NULL,
            FOREIGN KEY(collection_id) REFERENCES collections(id)
            ON DELETE CASCADE ON UPDATE CASCADE,
            FOREIGN KEY(tag_id) REFERENCES tags(id) 
            ON DELETE CASCADE ON UPDATE CASCADE)""")
        self.connection.commit()

    def get_file_ids(self, filenames):
        """Returns a dictionary of file ids to be passed to other methods.
           filenames  An iterable of absolute paths to the files."""
        cursor = self.connection.cursor()
        ids = dict()
        for filename in filenames:
            cursor.execute("""SELECT files.id FROM files, paths
                    WHERE paths.id = files.path AND
                    paths.name = ? AND files.name = ?""", 
                    os.path.split(filename))
            row = cursor.fetchone()
            if row is not None:
                ids[filename] = row[0]
            else:
                ids[filename] = None
        return ids

    def get_tag_ids(self, tags):
        """Returns a dictionary of tag ids to be passed to other methods.
           tags  An iterable of tag names."""
        cursor = self.connection.cursor()
        ids = dict()
        for t in tags:
            cursor.execute("select id from tags where name = ?", (t, ))
            ids[t] = cursor.fetchone()[0]
        return ids

    def get_full_paths(self, files):
        ret = list()
        for f in files:
            ret.append(os.path.join(f["path"], f["name"]))
        return ret

    def get_file_tags(self, fileid):
        cursor = self.connection.cursor()
        cursor.execute("""SELECT tags.name as name
                            FROM file_tags, tags
                            WHERE file_tags.tag_id = tags.id and
                              file_tags.file_id = ?""", (fileid,))
        res = [tag['name'] for tag in cursor]
        return res

    def create_tags(self, tags):
        """Creates new tag entries into the database.
           Called automatically by all tag adding methods.
           tags   an iterable of tag names."""
        cursor = self.connection.cursor()
        cursor.executemany("INSERT INTO tags(name) VALUES (?)", ((t,) for t in tags))

    def add_files(self, fileinfos):
        """Adds new files to the database.
           fileinfos   a dictionary with the keys name and tags.
                       Tags should be a list or a tuple."""
        cursor = self.connection.cursor()
        cursor.execute("BEGIN")
        file_tuples = list()
        tags = set()
        for fileinfo in fileinfos:
            name = os.path.basename(fileinfo["name"])
            path = os.path.dirname(fileinfo["name"])
            path = os.path.abspath(path)
            cursor.execute("INSERT INTO paths(name) VALUES(?)", (path,))
            cursor.execute("SELECT id FROM paths WHERE name = ?", (path,))
            path = cursor.fetchone()[0]
            i = self.get_file_ids([fileinfo["name"]])
            if i[fileinfo["name"]] is None:
                add_time = datetime.date.today()
                file_tuples.append((name, path, add_time, fileinfo["tags"]))
                tags.update(fileinfo["tags"])
        
        cursor.execute("BEGIN")
        cursor.executemany("INSERT INTO files(name, path, date) VALUES(?, ?, ?)",
            [f[:-1] for f in file_tuples])

        self.create_tags(tags)
        tag_ids = self.get_tag_ids(tags)

        file_id_list = list()
        for f in file_tuples:
            cursor.execute("SELECT id FROM files WHERE name = ? AND path = ? AND date = ?", f[:-1])
            file_id_list.append((cursor.fetchone()[0], f[-1]))

        def gen_id_pairs():
            for f in file_id_list:
                for t in f[-1]:
                    yield (f[0], tag_ids[t])

        cursor.executemany("INSERT INTO file_tags(file_id, tag_id) VALUES(?, ?)", gen_id_pairs())
        self.connection.commit()

    def remove_files(self, idict):
        """Removes files from the database.
           Does not remove files from disk.
           idict  a dictionary as returned by get_file_ids"""
        cursor = self.connection.cursor()
        cursor.execute("BEGIN")
        cursor.executemany("DELETE FROM files WHERE id = ?", [(i,) for i in idict.values()])
        self.connection.commit()

    def add_tags_to_file(self, item, tags):
        """Adds tags to the file identified by item.
           tags  iterable of the tags.
           item  id of the file from get_file_ids."""
        cursor = self.connection.cursor()
        self.create_tags(tags)
        cursor.execute("BEGIN")
        tag_ids = self.get_tag_ids(tags)
        cursor.executemany("INSERT INTO file_tags(file_id, tag_id) VALUES(?, ?)", 
                [(item, tag_ids[key]) for key in tag_ids.keys()])
        self.connection.commit()

    def remove_tags_from_file(self, item, tags):
        """Removes tags from a file.
           item  id of the item
           tags  an iterable of tag names"""
        cursor = self.connection.cursor()
        tag_ids = self.get_tag_ids(tags)
        cursor.execute("BEGIN")
        cursor.executemany("DELETE FROM file_tags WHERE file_id = ? AND tag_id = ?",
                ((item, tag_ids[key]) for key in tag_ids.keys()))
        self.connection.commit()

    def search_by_name(self, search_string):
        """Returns a list of dictionaries of all files that match search_string.
           search_string  a string with sql wildcards"""
        cursor = self.connection.cursor()
        cursor.execute("""SELECT files.id AS id, files.name AS name, paths.name AS path, files.date,
                          group_concat(tags.name) AS tags
                FROM files, paths, file_tags, tags
                WHERE paths.id = files.path AND file_tags.file_id = files.id AND
                      file_tags.tag_id = tags.id
                AND files.name GLOB :ss
                GROUP BY files.id""",
                { "ss":search_string })
        res = list()
        for row in cursor:
            res.append(dict(row))
            res[-1]['tags'] = res[-1]['tags'].split(',')
        return res

    def search_by_tags(self, tags, search_type = SEARCH_EXCLUSIVE):
        """Returns a list of all files that have any of the tags given.
           tags  an iterable with the tag names searched."""
        cursor = self.connection.cursor()
        query = """SELECT files.id AS id, files.name AS name, paths.name AS path,
                          files.date AS date, group_concat(tags.name) AS tags,
                          count(tags.id) AS tags_matched
            FROM files, file_tags, tags, paths 
            WHERE tags.id = file_tags.tag_id AND
            files.path = paths.id AND
            file_tags.file_id = files.id AND
            tags.name IN ({})
            GROUP BY files.id
            """.format(",".join(["?"] * len(tags)))
        cursor.execute(query, tags)
        res = list()
        for row in cursor:
            if search_type == SEARCH_INCLUSIVE or row["tags_matched"] == len(tags):
                res.append(dict(row))
                res[-1]['tags'] = res[-1]['tags'].split(',')
        return res

    def add_tags_to_collection(self, name, tags):
        cursor = self.connection.cursor()
        cursor.execute("SELECT id FROM collections WHERE name = ?", (name,))
        row = cursor.fetchone()
        if row is None:
            return 
        item = row[0]
        self.create_tags(tags)
        tag_ids = self.get_tag_ids(tags)
        cursor.executemany("INSERT INTO collection_tags(collection_id, tag_id) VALUES(?, ?)",
                ((item, tag_ids[key]) for key in tag_ids.keys()))
        self.connection.commit()

    def add_collection(self, name, tags):
        cursor = self.connection.cursor()
        cursor.execute("INSERT INTO collections(name) values(?)", (name,))
        self.create_tags(tags)
        self.connection.commit()
        self.add_tags_to_collection(name, tags)
    
    def remove_collection(self, name):
        cursor = self.connection.cursor()
        cursor.execute("SELECT COUNT(id) FROM collections WHERE name = ?", (name,))
        exists = cursor.fetchone()[0] > 0
        if exists:
            cursor.execute("DELETE FROM collections WHERE name = ?", (name, ))
            self.connection.commit()
        else:
            return

    def _list_names(self, table):
        """Returns a list of names in a table."""
        cursor = self.connection.cursor()
        # table name can not contain a ;
        if ';' in table:
            return []
        cursor.execute("SELECT name FROM " + table)
        res = list()
        for t in cursor:
            res.append(t[0])
        return res

    def list_tags(self):
        """Returns a list of all tags in the database."""
        return self._list_names("tags")

    def list_collections(self):
        """Returns a list of all collection data in the database."""
        names = self._list_names("collections")
        ret = list()
        for n in names:
            d = MyDict(name=n)
            d.id = n
            d.set_get_tags(lambda x: self.get_collection_tags(x))
            d.set_get_fc(lambda x: len(self.list_files_in_collection(x)))
            ret.append(d)
        return ret

    def list_files_in_collection(self, collection):
        tags = self.get_collection_tags(collection)
        return self.search_by_tags(tags, SEARCH_EXCLUSIVE)

    def get_collection_tags(self, collection):
        cursor = self.connection.cursor()
        cursor.execute("""SELECT tags.name as name
                        FROM collections, collection_tags, tags
                        WHERE collections.id = collection_tags.collection_id AND
                        collection_tags.tag_id = tags.id AND
                        collections.name = ?""", (collection, ))
        tags = list()
        for row in cursor:
            tags.append(row[0])
        return tags

    def export_collection(self, collection):
        """Creates an archive with all files and metadata of a collection.
           The achive is a gzipped tar containing the metadata file and 
           the seperate files in their directories."""
        with open(collection + ".csv", 'w', newline='') as collfile:
            writer = csv.writer(collfile, dialect=ExportDialect())
            writer.writerow(["name", "relpath", "tags"])
            files = self.list_files_in_collection(collection)
            pathlist = [f["path"] for f in files]
            common_root = os.path.commonprefix(pathlist)
            for path in pathlist:
                if "/media/files/kuvat/muut/instructor" not in path:
                    print(path)
            for f in files:
                tags = self.get_file_tags(f["id"])
                relpath = os.path.relpath(f["path"], common_root)
                writer.writerow([f["name"], relpath, ','.join(tags)])

    def import_collection(self, filename, common_root="."):
        """Adds an exported collection and its files to the database."""
        pass

