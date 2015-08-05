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
        db_ids = self.ids_from_gallery(self.main.get_current_view())
        self.db.add_tags_to_files(sorted(db_ids.values()), tagview.selection())
        self.update_selection_tags(event)

    def add_tags_from_entry(self, event):
        entry = event.widget
        tag_string = entry.get()
        tag_list = tag_string.split(',')
        tags = [t.strip() for t in tag_list]
        file_ids = self.ids_from_gallery(self.main.get_current_view())
        self.db.add_tags_to_files(sorted(file_ids.values()), tags)
        self.main.close_query()
        self.main.get_sidebar_view('main_tags').append_tags(tags)
        self.update_selection_tags(event)

    def ids_from_gallery(self, gallery):
        paths = gallery.selection()
        ids = self.db.get_file_ids(paths)
        return ids

    def rename_tag(self, event):
        entry = event.widget
        new_name = entry.get()
        old_name = entry.original_value
        new_name = new_name.strip()
        if new_name in self.db.list_tags():
            self.db.join_tags(new_name, old_name)
        else:
            self.db.rename_tags(((old_name, new_name), ))
        self.main.close_query()
        tagview = self.main.get_sidebar_view('main_tags')
        tagview.delete(old_name)
        tagview.append_tags((new_name, ))
        self.update_selection_tags(event)

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
        directory = askdirectory(title="Select a directory to add.")
        if len(directory) == 0:
            return
        fileinfos = list()
        tag_list = self.query_tags()
        for root, directories, filenames in os.walk(directory):
            for name in filenames:
                path = os.path.join(root, name)
                f_type = guess_type(path)
                if f_type[0] is not None and 'image' in f_type[0]:
                    fileinfos.append({'name':path, 'tags':tag_list})
        self.db.add_files(fileinfos)
        self.main.get_sidebar_view('main_tags').append_tags(tag_list)

    def _remove_tags(self, ids, tags):
        self.db.remove_tags_from_files(sorted(ids.values()), tags)

    def remove_tags_from_files(self, event):
        view = self.main.get_current_view()
        names = view.selection()
        ids = self.db.get_file_ids(names)
        tags = self.db.get_file_tags(ids.values())
        tagset = set(*[t['tags'].split(',') for t in tags])
        dialog = ListDialog(self.main.root, tagset, 
                'Select tags to remove from\n{}'.format(',\n'.join(names)),
                lambda t: self._remove_tags(ids, t))


    def remove_deleted_files(self):
        if askyesno('Remove deleted files?',
                'Are you sure you want to remove deleted files from the database? This cannot be undone'):
            removed = self.db.remove_deleted_files()
            showinfo('Removed files.', 
                    "The following files have been removed:\n{}".format('\n'.join(removed)))

    def show_selection_tags(self, event=None):
        if len(self.main.views) == 0:
            return
        selection = self.ids_from_gallery(self.main.get_current_view())
        if len(selection) == 0:
            return
        fids = tuple(selection.values())
        tags = self.db.get_file_tags(fids)
        tagset = set(tags[0]['tags'].split(','))
        tagset.intersection_update(*[t['tags'].split(',') for t in tags])
        view = TagView(self.main.sidebar, tuple(tagset))
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
           or self.main.get_current_view() is None):
            return
        selection = self.ids_from_gallery(self.main.get_current_view())
        if len(selection) == 0:
            self.main.remove_sidebar_view('selection_tags')
            return
        logger.debug('Selection size:', len(selection))
        tagview = self.main.get_sidebar_view('selection_tags')
        fids = tuple(selection.values())
        new_tags = self.db.get_file_tags(fids)
        tags = set(new_tags[0]['tags'].split(','))
        tags.intersection_update(*[t['tags'].split(',') for t in new_tags])
        tagview.set(tags)

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

