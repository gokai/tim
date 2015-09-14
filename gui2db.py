import os
import logging
from mimetypes import guess_type
from time import process_time
logger = logging.getLogger(__name__)

from tkinter.filedialog import askopenfilenames, askdirectory
from tkinter.messagebox import askyesno, showwarning, showinfo
from tkinter.simpledialog import askstring

from dialog import ListDialog
from tagview import TagView, NameView
from editview import CollectionEditView

class Gui2Db(object):
    def __init__(self, db, main, gallery_func):
        self.db = db
        self.main = main
        self.all_ids = {}
        self.gallery_func = gallery_func

    def _create_gallery(self, files):
        paths = [os.path.join(d['path'], d['name']) for d in files]
        paths = set(paths)
        gal = self.gallery_func(self.main.root, sorted(paths))
        self.main.new_view(gal)
        self.fill_all_ids(gal)

    def search_tags(self, tags):
        files = self.db.search_by_tags(tags)
        self._create_gallery(files)

    def fill_all_ids(self, gallery):
        pathset = set(gallery.paths).difference(self.all_ids.keys())
        id_generator = self.db.generate_file_ids(sorted(pathset))

        def add_next_id():
            try:
                pair = next(id_generator)
                self.all_ids[pair[0]] = pair[1]
                self.main.root.after(50, add_next_id)
            except StopIteration:
                pass

        self.main.root.after_idle(add_next_id)

    def search_event(self, event):
        tags = event.widget.view.selection()
        self.search_tags(tags)

    def search_tagstring(self, event):
        self.main.text_query('Search with tags: ', 
                accept_func = lambda ts, o: self.search_tags(ts.split(',')),
                complete_list = self.main.get_sidebar_view('main_tags').get_names()
        )

    def search_collection(self, event):
        collections = self.main.get_sidebar_view('collections').selection()
        files = []
        for collection in collections:
            tags = self.db.get_collection_tags(collection)
            files.extend(self.db.search_by_tags(tags))
        self._create_gallery(files)

    def add_tags_from_tagview(self, event, tagview):
        db_ids = self.ids_from_gallery(self.main.get_current_view())
        self.db.add_tags_to_files(sorted(db_ids.values()), tagview.selection())
        self.update_selection_tags(event)
        self.update_tagview(tagview, tagview.selection(), len(db_ids))

    def add_tags_from_entry(self, event):
        entry = event.widget
        tag_string = entry.get()
        tag_list = tag_string.split(',')
        tags = [t.strip() for t in tag_list]
        file_ids = self.ids_from_gallery(self.main.get_current_view())
        self.db.add_tags_to_files(sorted(file_ids.values()), tags)
        self.main.close_query()
        tagview = self.main.get_sidebar_view('main_tags')
        tagview.append_tags(tags)
        self.update_selection_tags(event)
        self.update_tagview(tagview, tags, len(file_ids))

    def update_tagview(self, tagview, tags, file_count):
        tagview.update_counts(tags,
                (tagview.get_count(n) + file_count for n in tags))

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
        tagview = self.main.get_sidebar_view('main_tags')
        self.update_tagview(tagview, tags, -len(ids))
        self.db.remove_tags_from_files(sorted(ids.values()), tags)

    def remove_tags_from_files(self, event):
        view = self.main.get_current_view()
        names = view.selection()
        ids = self.db.get_file_ids(names)
        tags = self.db.get_file_tags(ids.values())
        tagset = set(tags[0]['tags'].split(','))
        tagset.intersection_update(*[t['tags'].split(',') for t in tags])
        dialog = ListDialog(self.main.root, tagset, 
                'Select tags to remove from\n{}'.format(',\n'.join(names)),
                lambda t: self._remove_tags(ids, t))


    def remove_deleted_files(self):
        if askyesno('Remove deleted files?',
                'Are you sure you want to remove deleted files from the database? This cannot be undone'):
            removed = self.db.remove_deleted_files()
            showinfo('Removed files.', 
                    "The following files have been removed:\n{}".format('\n'.join(removed)))
        return

    def show_selection_tags(self):
        if len(self.main.views) == 0:
            return
        gallery = self.main.get_current_view()
        selection = gallery.selection()
        if len(selection) == 0:
            return
        fids = (self.all_ids[p] for p in selection)
        tags = self.db.get_file_tags(fids)
        tagset = set(tags[0]['tags'].split(','))
        tagset.intersection_update(*[t['tags'].split(',') for t in tags])
        view = TagView(self.main.sidebar, tuple(tagset), 'Selection tags')
        self.main.add_sidebar(view, 'selection_tags')

    def _toggle(self, name, show):
        if self.main.get_sidebar_view(name) is not None:
            self.main.remove_sidebar_view(name)
        else:
            show()

    def toggle_selection_tags(self, event):
        self._toggle('selection_tags', lambda : self.show_selection_tags())

    def update_selection_tags(self, event):
        if (self.main.get_sidebar_view('selection_tags') is None
           or self.main.get_current_view() is None):
            return
        gallery = self.main.get_current_view()
        selection = gallery.selection()
        if len(selection) == 0:
            self.main.remove_sidebar_view('selection_tags')
            return
        tagview = self.main.get_sidebar_view('selection_tags')
        fids = (self.all_ids[p] for p in selection)
        new_tags = self.db.get_file_tags(fids)
        if len(new_tags) == 0:
            self.main.remove_sidebar_view('selection_tags')
            return
        tags = set(new_tags[0]['tags'].split(','))
        for tl in new_tags:
            tags.intersection_update(tl['tags'].split(','))
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
        names, counts = list(), list()
        for c in colls:
            names.append(c['name'])
            counts.append(c['file_count'])
        view = NameView(self.main.sidebar, names, 'Collections', counts)
        self.main.add_sidebar(view, 'collections')

    def toggle_collections(self, event):
        self._toggle('collections', lambda : self.show_collections())

    def add_to_collections(self, event):
        sidebar = self.main.get_sidebar_view('collections')
        files = self.ids_from_gallery(self.main.get_current_view())
        collections = []
        def add(colls):
            for c in colls:
                self.db.add_files_to_collection(c, files)

        if sidebar is not None:
            collections = sidebar.selection()
            add(collections)
        else:
            self.main.text_query('Add to collection(s): ', '', lambda coll_s, o: add(coll_s.split(',')))

    def edit_collection(self, event):
        sidebar = self.main.get_sidebar_view('collections')
        collection = sidebar.selection()[0]
        tags = self.db.get_collection_tags(collection)
        all_tags = self.db.list_tags()
        view = CollectionEditView(self.main.sidebar, collection, tags, all_tags, self.update_collection)
        self.main.add_sidebar(view, 'collection_edit')

    def update_collection(self, editview):
        old_tags = editview.old_tags
        old_name = editview.old_name
        new_tags = editview.new_tags()
        new_name = editview.new_name()
        if old_name != new_name:
            self.db.rename_collection(old_name, new_name)
        if new_tags != old_tags:
            remove_tags = set(old_tags).difference(new_tags)
            add_tags = set(new_tags).difference(old_tags)
            if len(remove_tags) > 0:
                self.db.remove_tags_from_collection(new_name, remove_tags)
            if len(add_tags) > 0:
                self.db.add_tags_to_collection(new_name, add_tags)

    def export_collections(self, event):
        all_collections = self.db.list_collections()
        collnames = [c['name'] for c in all_collections]
        def accept_cb(coll_str, orig):
            colls = coll_str.split(',')
            if len(colls) > 0:
                directory = askdirectory(title='Select destination directory.')
                for coll in colls:
                    if coll in collnames:
                        self.db.export_collection(coll,to_dir=directory)
                        showinfo('Collection export', 'Collection {} exported'.format(coll))
                    else:
                        showwarning('Collection export', 'Collection {} does not exist'.format(coll))

        collview = self.main.get_sidebar_view('collections')
        selected = []
        if collview is not None:
            selected = collview.selection()
        self.main.text_query('Export collections: ', ','.join(selected), accept_cb)

    def import_collections(self, event):
        all_collections = self.db.list_collections()
        collnames = [c['name'] for c in all_collections]
        filenames = askopenfilenames(defaultextension='.tar.gz', 
                filetypes=[('Gzipped tar', '*.tar.gz')], title='Import collections')
        for fname in filenames:
            name = os.path.basename(fname)
            name = name.split('.')[0]
            if name in collnames:
                showwarning('Import collection.', 'Collection named {} already exists, not importing.'.format(name))
            else:
                directory = askdirectory(title='Select directory for images in collection {}'.format(name))
                if directory != '':
                    self.db.import_collection(fname, directory)
                    tagview = self.main.get_sidebar_view('main_tags')
                    tagview.set(self.db.list_tags())
                    showinfo('Import collection.', 'Collection {} imported'.format(name))


