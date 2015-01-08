import os
from tkgraphics import gallery_with_slideshow

class Gui2Db(object):
    def __init__(self, db, main):
        self.db = db
        self.main = main

    def search(self, event):
        tags = event.widget.selection()
        files = self.db.search_by_tags(tags)
        paths = [os.path.join(d['path'], d['name']) for d in files]
        self.main.new_view(gallery_with_slideshow(self.main.root, paths, self.main.new_view))

    def add_tags_from_tagview(self, event, tagview):
        db_ids = self.ids_from_gallery(event.widget)
        for id_key in db_ids:
            self.db.add_tags_to_file(db_ids[id_key], tagview.widget.selection())

    def add_tags_from_entry(self, event):
        entry = event.widget
        tag_string = entry.get()
        tag_list = tag_string.split(',')
        file_ids = self.ids_from_gallery(self.main.views[self.main.cur_view])
        for fid_key in file_ids:
            self.db.add_tags_to_file(file_ids[fid_key], tag_list)
        self.main.close_query()
        self.main.sidebar.append_tags(tag_list)

    def ids_from_gallery(self, gallery):
        gal_ids = gallery.selection
        paths = [gallery.get_path(i) for i in gal_ids]
        return self.db.get_file_ids(paths)

    def rename_tag(self, event):
        entry = event.widget
        new_name = entry.get()
        old_name = entry.original_value
        self.db.rename_tags(((old_name, new_name), ))
        self.main.close_query()
        self.main.sidebar.widget.delete(old_name)
        self.main.sidebar.append_tags((new_name, ))

    def add_or_rename_tags(self, event):
        if event.widget.original_value is not None:
            self.rename_tag(event)
        else:
            self.add_tags_from_entry(event)



