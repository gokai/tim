# tim
Formerly known as CICM in Sourceforge by Tachara.

TIM is a tag based image management software.
It is written in python and it uses tkinter fot its GUI.
The tag information is stored in an SQLite database.

## Features

-   Any number of tags for any image
-   Thumbnail view of the images 
-   Full size view of images
-   Searching images by tags
-   Fully usable by keyboard(mostly implemented)
-   Fully usable by mouse(partially implemented)
-   Collections(partially implemented)
-   Export and import collections(not implemented)
-   Open images in another program(not implemented)

Collections are a way to group tags and use those groups to
find images. Basically they are stored search queries.
Export and import will enable sharing images and their tags.

## Usage

Run 

```
tim.py [database]
```

The database argument is the filename of the database to use.
If the file exists it has to be a valid TIM database or the
program will crash.
If the file does not exist it will be created.

## Database

The database is a basic sqlite database file with the following
structure

-   tags(id INTEGER, name TEXT)
-   files(id INTEGER, name TEXT, path INTEGER, date INTEGER)
    foreing key(path) references paths(id)
-   paths(id INTEGER, name TEXT)
-   file_tags(file_id INTEGER, tag_id INTEGER)
    foreing key(file_id) references files(id)
    foreing key(tag_id) references tags(id)
-   collections(id INTEGER, name TEXT)
-   collection_tags(collection_id INTEGER, tag_id)
    foreing key(collection_id) references collections(id)
    foreing key(tag_id) references tags(id)

See db.py for more details.
