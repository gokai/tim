#!/usr/bin/python
# A simple database class to handle tagging files.

#TODO: return values?

import sqlite3
import os
import datetime
import tarfile
import shutil
import tempfile
import csv
import logging
logger = logging.getLogger(__name__)

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
        """
        self.connection = sqlite3.connect(dbname)
        self.connection.row_factory = sqlite3.Row
        cursor = self.connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        self.connection.commit()
        self.initialize()

    def initialize(self):
        """Creates the tables used into the database file."""
        cursor = self.connection.cursor()
        cursor.execute("BEGIN")
        cursor.execute("""CREATE TABLE IF NOT EXISTS paths(id INTEGER PRIMARY KEY,
                name TEXT NOT NULL UNIQUE ON CONFLICT IGNORE)""")
        cursor.execute("""CREATE TABLE IF NOT EXISTS files(id INTEGER PRIMARY KEY,
            name TEXT NOT NULL, path INTEGER NOT NULL, date INTEGER NOT NULL,
            FOREIGN KEY(path) REFERENCES paths(id)
            ON UPDATE CASCADE ON DELETE CASCADE)""")
        # If a tag is added with a name already in the database
        # -> IGNORE since the tag is already present.
        cursor.execute("""CREATE TABLE IF NOT EXISTS tags(id INTEGER PRIMARY KEY,
            name TEXT NOT NULL UNIQUE ON CONFLICT IGNORE)""")
        cursor.execute("""CREATE TABLE IF NOT EXISTS file_tags(
            file_id INTEGER NOT NULL, tag_id INTEGER NOT NULL,
            FOREIGN KEY(file_id) REFERENCES files(id) 
            ON DELETE CASCADE ON UPDATE CASCADE,
            FOREIGN KEY(tag_id) REFERENCES tags(id) 
            ON DELETE CASCADE ON UPDATE CASCADE)""")
        cursor.execute("""CREATE TABLE IF NOT EXISTS collections(
            id INTEGER PRIMARY KEY, 
            name TEXT NOT NULL UNIQUE ON CONFLICT IGNORE)""")
        cursor.execute("""CREATE TABLE IF NOT EXISTS collection_tags(
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

    def generate_file_ids(self, filenames):
        """A generator method that yields (path, id) pairs.
           filenames  An iterable of absolute paths to the files."""
        cursor = self.connection.cursor()
        for filename in filenames:
            cursor.execute("""SELECT files.id FROM files, paths
                    WHERE paths.id = files.path AND
                    paths.name = ? AND files.name = ?""", 
                    os.path.split(filename))
            row = cursor.fetchone()
            if row is not None:
                yield (filename, row[0])
            else:
                yield (filename, None)

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

    def get_file_tags(self, fileids):
        cursor = self.connection.cursor()
        cursor.execute("CREATE TEMPORARY TABLE tmp_file_ids(INTEGER)")
        cursor.executemany("INSERT INTO tmp_file_ids VALUES (?)", ((i, ) for i in fileids))
        cursor.execute("""SELECT file_tags.file_id AS id, group_concat(tags.name) AS tags
                        FROM file_tags, tags
                        WHERE file_tags.tag_id = tags.id AND
                          file_tags.file_id IN tmp_file_ids
                        GROUP BY file_tags.file_id""")
        res = [dict(row) for row in cursor]
        cursor.execute("DROP TABLE tmp_file_ids")
        self.connection.commit()
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

    def add_tags_to_files(self, items, tags):
        """Adds tags to the files identified by item.
           tags  iterable of the tags.
           items  ids of the file from get_file_ids."""
        cursor = self.connection.cursor()
        self.create_tags(tags)
        tag_ids = self.get_tag_ids(tags)
        cursor.execute("BEGIN")
        for item in items:
            cursor.executemany("INSERT INTO file_tags(file_id, tag_id) VALUES(?, ?)", 
                    [(item, tag_ids[key]) for key in tag_ids.keys()])
        self.connection.commit()

    def remove_tags_from_files(self, items, tags):
        """Removes tags from a file.
           items  ids of the item
           tags  an iterable of tag names"""
        cursor = self.connection.cursor()
        tag_ids = self.get_tag_ids(tags)
        cursor.execute("BEGIN")
        for item in items:
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
        """Returns a list of all files that have the tags given.
           tags         an iterable with the tag names searched.
           search_type  if SEARCH_EXCLUSIVE requires exact match of tags
                        for a file to be returned"""
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

    def remove_tags_from_collection(self, name, tags):
        cursor = self.connection.cursor()
        cursor.execute("SELECT id FROM collections WHERE name = ?", (name,))
        row = cursor.fetchone()
        if row is None:
            return
        item = row[0]
        tag_ids = self.get_tag_ids(tags)
        cursor.executemany("DELETE FROM collection_tags WHERE collection_id = ? AND tag_id = ?",
                ((item, tag_ids[key]) for key in tag_ids))


    def add_collection(self, name, tags):
        cursor = self.connection.cursor()
        cursor.execute("INSERT INTO collections(name) values(?)", (name,))
        self.create_tags(tags)
        self.connection.commit()
        self.add_tags_to_collection(name, tags)

    def add_files_to_collection(self, collection, files):
        tags = self.get_collection_tags(collection)
        tag_ids = self.get_tag_ids(tags)
        cursor = self.connection.cursor()
        data = []
        for f in files:
            for tid in tag_ids.values():
                data.append((files[f], tid))
        cursor.executemany("INSERT INTO file_tags(file_id, tag_id) VALUES(?, ?)", data)
        self.connection.commit()
    
    def remove_collection(self, name):
        cursor = self.connection.cursor()
        cursor.execute("SELECT COUNT(id) FROM collections WHERE name = ?", (name,))
        exists = cursor.fetchone()[0] > 0
        if exists:
            cursor.execute("DELETE FROM collections WHERE name = ?", (name, ))
            self.connection.commit()
        else:
            return

    def list_tags(self):
        """Returns a list of all tags in the database."""
        cursor = self.connection.cursor()
        cursor.execute("""SELECT tags.name AS name, COUNT(file_tags.file_id) AS file_count
                       FROM tags, file_tags
                       WHERE tags.id = file_tags.tag_id
                       GROUP BY tags.id""")
        ret = list()
        for row in cursor:
            ret.append({'name':row[0], 'file_count':row[1]})
        return ret

    def list_collections(self):
        """Returns a list of all collection data in the database."""
        cursor = self.connection.cursor()
        cursor.execute("""SELECT collections.name AS name, group_concat(tags.name) AS tags
                        FROM collections, tags, collection_tags
                        WHERE collections.id = collection_tags.collection_id AND
                        tags.id = collection_tags.tag_id
                        GROUP BY collections.id
                        ORDER BY collections.id""")
        ret = list()
        for row in cursor:
            if row[0] is not None:
                ret.append({'name':row[0], 'tags':row[1],
                    'file_count': len(self.search_by_tags(row[1].split(',')))})
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

    def list_all_files(self):
        """Returns a list of all files in the database."""
        cursor = self.connection.cursor()
        cursor.execute("""SELECT files.id AS id, files.name AS name, paths.name AS path,
                                 files.date AS date, group_concat(tags.name) AS tags
                          FROM files, file_tags, tags, paths
                          WHERE tags.id = file_tags.tag_id AND files.path = paths.id AND
                               file_tags.file_id = files.id
                          GROUP BY files.id
                        """)
        res = list()
        for row in cursor:
            res.append(dict(row))
            res[-1]['tags'] = res[-1]['tags'].split(',')
        return res

    def remove_deleted_files(self):
        """Removes files no longer present on filesystem from database."""
        files = self.list_all_files()
        paths = self.get_full_paths(files)
        removed = dict()
        ret_val = list()
        for i, path in enumerate(paths):
            if not os.path.exists(path):
                removed[path] = files[i]['id']
                ret_val.append(path)
        self.remove_files(removed)
        return ret_val


    def rename_tags(self, tag_pairs):
        """Renames tags given in tag_pairs with values from tag_pairs.
         tag_pairs    an iterable of (old_name, new_name) pairs."""
        cursor = self.connection.cursor()
        cursor.executemany("""UPDATE tags SET name=?2 WHERE name=?1""", tag_pairs)
        self.connection.commit()
    
    def join_tags(self, tag1, tag2):
        """Combines two tags into one, removing tag2 from database.
        All references to tag2 are changed to refer to tag1.
        tag1    the first tag
        tag2    the second tag. Will be removed."""
        cursor = self.connection.cursor()
        ids = self.get_tag_ids((tag1, tag2))
        cursor.execute("""UPDATE file_tags SET tag_id = ?1 WHERE tag_id = ?2""", (ids[tag1], ids[tag2]))
        cursor.execute("""UPDATE collection_tags SET tag_id=?1 WHERE tag_id = ?2""", (ids[tag1], ids[tag2]))
        cursor.execute("""DELETE FROM tags WHERE id = ?""", (ids[tag2], ))
        self.connection.commit()

    def export_collection(self, collection, to_dir=os.path.curdir, tmp_location=None):
        """Creates an archive with all files and metadata of a collection.
           The archive is a gzipped tar containing the metadata file and 
           the seperate files in their directories."""
        prev_wd = os.getcwd()
        with tempfile.TemporaryDirectory(dir=tmp_location) as tmp_dir:
            os.chdir(tmp_dir)
            archivename = collection + ".tar.gz"
            with tarfile.open(archivename, "w:gz") as archive:
                fname = collection + ".csv"
                with open(fname, 'w', newline='') as collfile:
                    writer = csv.writer(collfile, dialect=ExportDialect())
                    writer.writerow(["name", "relpath", "tags"])
                    writer.writerow(["tt", "__COLLECTION__", ",".join(self.get_collection_tags(collection))])
                    files = self.list_files_in_collection(collection)
                    pathlist = [f["path"] for f in files]
                    common_root = find_common_root(pathlist)
                    tags = self.get_file_tags(f["id"] for f in files)
                    for f_ind, f in enumerate(files):
                        relpath = os.path.relpath(f["path"], common_root)
                        tagstring = tags[f_ind]["tags"]
                        writer.writerow([f["name"], relpath, tagstring])
                        if not os.path.exists(relpath):
                            os.makedirs(relpath)
                        shutil.copyfile(os.path.join(f["path"], f["name"]),
                                        os.path.join(os.path.curdir, relpath, f["name"]))
                        archive.add(os.path.join(os.path.curdir, relpath, f["name"]))
                archive.add(fname)
                shutil.copyfile(fname, os.path.join(prev_wd, fname))
            os.chdir(prev_wd)
            shutil.copyfile(os.path.join(tmp_dir, archivename), os.path.join(to_dir, archivename))

    def import_collection(self, filename, file_dir):
        """Adds an exported collection and its files to the database."""
        collname = os.path.splitext(os.path.basename(filename))[0]
        collname = os.path.splitext(collname)[0]
        prev_wd = os.getcwd()
        fileinfos = []
        coll_tags = []
        with tempfile.TemporaryDirectory() as tmp_dir:
            os.chdir(tmp_dir)
            with tarfile.open(os.path.join(prev_wd, filename), 'r:gz') as archive:
                coll = collname + '.csv'
                archive.extract(coll, path=tmp_dir)
                with open(os.path.join(tmp_dir, coll), 'r', newline='') as collfile:
                    # Since csv.reader does not support lineterminator
                    # a custom iterator is needed
                    content = collfile.read()
                    reader = csv.reader((r for r in content.split(ExportDialect.lineterminator)),
                            dialect=ExportDialect())
                    for index, row in enumerate(reader):
                        if len(row) != 3 or index == 0:
                            continue
                        elif row[1] == '__COLLECTION__':
                            coll_tags = row[2].split(',')
                        elif not os.path.isabs(row[1]):
                            f_path = os.path.join(file_dir, row[1])
                            if not os.path.exists(f_path):
                                os.makedirs(f_path)
                            archive.extract(os.path.join(os.path.curdir, row[1], row[0]), path=file_dir)
                            fileinfos.append({'name':os.path.join(f_path, row[0]), 'tags':row[2].split(',')})
            os.chdir(prev_wd)
        self.add_files(fileinfos)
        self.add_collection(collname, coll_tags)


def find_common_root(paths):
    prefix = os.path.commonprefix(paths)
    root = prefix
    if not os.path.isdir(prefix):
        root = os.path.dirname(prefix)
    return root

