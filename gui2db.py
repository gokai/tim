
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

    def add_tags(event, tagview):
        gal_ids = event.widget.selection
        paths = [event.widget.get_path(i) for i in gal_ids]
        db_ids = self.db.get_file_ids(paths)
        for path in db_ids:
            self.db.add_tags_to_file(db_ids[path], tagview.selection())

