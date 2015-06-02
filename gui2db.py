import os
from mimetypes import guess_type

from tkinter.filedialog import askopenfilenames, askdirectory
from tkinter.messagebox import askyesno, showwarning, showinfo
from tkinter.simpledialog import askstring

from tkgraphics import gallery_with_slideshow
from dialog import ListDialog
from tagview import TagView, NameView

class Gui2Db(object):
    def __init__(self, db, main):
        self.db = db
        self.main = main

    def search(self, event):
        tags = self.main.active_sidebar().selection()
        files = self.db.search_by_tags(tags)
        paths = [os.path.join(d['path'], d['name']) for d in files]
        self.main.new_view(gallery_with_slideshow(self.main.root, paths, self.main.new_view))

    def add_tags_from_tagview(self, event, tagview):
        db_ids = self.ids_from_gallery(event.widget)
        for id_key in db_ids:
            self.db.add_tags_to_file(db_ids[id_key], tagview.selection())

    def add_tags_from_entry(self, event):
        entry = event.widget
        tag_string = entry.get()
        tag_list = tag_string.split(',')
        file_ids = self.ids_from_gallery(self.main.views[self.main.cur_view])
        for fid_key in file_ids:
            self.db.add_tags_to_file(file_ids[fid_key], tag_list)
        self.main.close_query()
        self.main.get_sidebar_view('main_tags').append_tags(tag_list)

    def ids_from_gallery(self, gallery):
        paths = gallery.selection()
        ids = self.db.get_file_ids(paths)
        return ids

    def rename_tag(self, event):
        entry = event.widget
        new_name = entry.get()
        old_name = entry.original_value
        if new_name in self.db.list_tags():
            self.db.join_tags(new_name, old_name)
        else:
            self.db.rename_tags(((old_name, new_name), ))
        self.main.close_query()
        tagview = self.main.get_sidebar_view('main_tags')
        tagview.delete(old_name)
        tagview.append_tags((new_name, ))

    def add_or_rename_tags(self, event):
        if event.widget.original_value is not None:
            self.rename_tag(event)
        else:
            self.add_tags_from_entry(event)

    def query_tags(self):
        selected_tags = self.main.get_sidebar_view('main_tags').selection()
        new_tags = list()
        add_sel_tags = False
        tag_string = askstring('New tags?', 'Give tags to new files:')
        tag_list = list()
        if tag_string is not None:
            tag_list = tag_string.split(',')
        if len(selected_tags) > 0:
           if askyesno('Add selected tags?', 
                    'Do you want to add selected tags to added files?'):
                tag_list.extend(selected_tags)
        if len(tag_list) == 0:
            showwarning('No tags given!', 'Please give at least one tag to the new files.')
            tag_list = self.query_tags()
        return tag_list

    def add_files(self, event):
        filenames = askopenfilenames()
        if filenames == '':
            return
        fileinfos = list()
        tag_list = self.query_tags()
        for name in filenames:
            if os.path.isdir(name):
                continue
            else:
                fileinfos.append({'name':name, 'tags':tag_list})
        self.db.add_files(fileinfos)
        self.main.get_sidebar_view('main_tags').append_tags(tag_list)

    def add_directory(self, event):
        directory = askdirectory()
        if len(directory) == 0:
            return
        fileinfos = list()
        tag_list = self.query_tags()
        for name in os.listdir(directory):
            path = os.path.join(directory, name)
            f_type = guess_type(path)
            if not os.path.isdir(path) and f_type[0] is not None and 'image' in f_type[0]:
                fileinfos.append({'name':path, 'tags':tag_list})
        self.db.add_files(fileinfos)
        self.main.get_sidebar_view('main_tags').append_tags(tag_list)

    def _remove_tags(self, ids, tags):
        for key in ids:
            self.db.remove_tags_from_file(ids[key], tags)

    def remove_tags_from_files(self, event):
        view = self.main.views[self.main.cur_view]
        names = [view.get_path(i) for i in view.selection]
        ids = self.db.get_file_ids(names)
        tags = set()
        for key in ids:
            tags.update(self.db.get_file_tags(ids[key]))
        tags = tuple(tags)
        dialog = ListDialog(self.main.root, tags, 
                'Select tags to remove from\n{}'.format(',\n'.join(names)),
                lambda t: self._remove_tags(ids, t))


    def remove_deleted_files(self):
        if askyesno('Remove deleted files?',
                'Are you sure you want to remove deleted files from the database? This cannot be undone'):
            removed = self.db.remove_deleted_files()
            showinfo('Removed files.', 
                    "The following files have been removed:\n{}".format('\n'.join(removed)))

    def _get_tags_from_db(self, selection):
        tags = set()
        for fid in selection.values():
            ftags = self.db.get_file_tags(fid)
            if len(tags) == 0:
                tags.update(ftags)
            else:
                tags.intersection_update(ftags)
        return tags

    def show_selection_tags(self, event=None):
        if len(self.main.views) == 0:
            return
        selection = self.ids_from_gallery(self.main.views[self.main.cur_view])
        if len(selection) == 0:
            return
        tags = self._get_tags_from_db(selection)
        view = TagView(self.main.sidebar, list(tags))
        self.main.add_sidebar(view, 'selection_tags')

    def _toggle(self, name, show):
        if self.main.get_sidebar_view(name) is not None:
            self.main.remove_sidebar_view(name)
        else:
            show()

    def toggle_selection_tags(self, event):
        self._toggle('selection_tags', self.show_selection_tags)

    def update_selection_tags(self, event):
        if (self.main.get_sidebar_view('selection_tags') is None
           or len(self.main.views) == 0):
            return
        selection = self.ids_from_gallery(self.main.views[self.main.cur_view])
        if len(selection) == 0:
            self.main.remove_sidebar_view('selection_tags')
            return
        tagview = self.main.get_sidebar_view('selection_tags')
        cur_tags = set(tagview.get_tag_list())
        new_tags = self._get_tags_from_db(selection)
        add_tags = new_tags.difference(cur_tags)
        del_tags = cur_tags.difference(new_tags)
        for tag in del_tags:
            tagview.delete(tag)
        tagview.append_tags(add_tags)

    def add_collection(self):
        tagview = self.main.get_sidebar_view('main_tags')
        tags = tagview.selection()
        def add_callback(name, orig):
            name = name.strip()
            if name == "" or len(tags) == 0:
                return 
            self.db.add_collection(name, tags)
        self.main.text_query('Collection name: ', '', add_callback)

    def remove_collection(self):
        def remove_callback(name, orig):
            name = name.strip()
            if name == "" or not askyesno('Remove collection: {}'.format(name)):
                return
            self.db.remove_collection(name)
        self.main.text_query('Remove collection: ', '', remove_callback)

    def show_collections(self):
        colls = self.db.list_collections()
        if len(colls) == 0:
            return
        view = NameView(self.main.sidebar, [c['name'] for c in colls])
        self.main.add_sidebar(view, 'collections')

    def toggle_collections(self, event):
        self._toggle('collections', self.show_collections)

