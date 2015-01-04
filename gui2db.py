
from tkgraphics import gallery_with_slideshow

class Gui2Db(object):
    def __init__(self, db, main):
        self.db = db
        self.main = main

    def search(event):
        tags = event.widget.selection()
        files = self.db.search_by_tags(tags)
        paths = [os.path.join(d['path'], d['name']) for d in files]
        gui.new_view(gallery_with_slideshow(paths))

    def add_tags_from_tagview(event, tagview):
        db_ids = self.ids_from_gallery(event.widget)
        for id_key in db_ids:
            self.db.add_tags_to_file(db_ids[id_key], tagview.selection())

    def add_tags_from_entry(event, file_ids):
        entry = event.widget
        tag_string = entry.get()
        tag_list = tag_string.split(',')
        for fid_key in file_ids:
            self.db.add_tags_to_file(file_ids[fid_key], tag_list)

    def ids_from_gallery(gallery):
        gal_ids = gallery.selection
        paths = [gallery.get_path(i) for i in gal_ids]
        return self.db.get_file_ids(paths)



