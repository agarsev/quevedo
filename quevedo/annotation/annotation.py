# 2020-11-11 Antonio F. G. Sevilla <afgs@ucm.es>
# Licensed under the Open Software License version 3.0

from enum import Flag
import json
from pathlib import Path
from shutil import copyfile

Target = Flag('AnnotationTarget', 'LOGO GRAPH')


class Annotation:
    '''Class representing a single annotation of either a logogram of a
    sign or signs in the dataset or an isolated grapheme.

    Args:
        path: the full path to the annotation files (either source image or tag
            dictionary, which should share path and filename but not extension
            (the annotation dictionary need not exist).
        '''

    target = None  # Should be set by concrete class

    def __init__(self, path):
        path = Path(path)
        #: Number which identifies this annotation in its subset
        self.id = path.stem
        self.json_path = path.with_suffix('.json')
        self.image_path = path.with_suffix('.png')
        #: Dictionary of metadata annotations
        self.meta = {}
        #: Train/test split to which the annotation belongs
        self.set = 'train'
        if self.json_path.exists():
            self.update(**json.loads(self.json_path.read_text()))

    def update(self, *, meta=None, set=None, **kwds):
        if meta:
            self.meta = meta
        if set:
            self.set = set

    def to_dict(self):
        return {'meta': self.meta, 'set': self.set}

    def save(self):
        self.json_path.write_text(json.dumps(self.to_dict()))

    def create_from(self, *, image_path=None, binary_data=None,
                    pil_image=None, **kwds):
        if image_path is not None:
            copyfile(image_path, self.image_path)
            self.update(meta={'filename': image_path.stem})
        elif binary_data is not None:
            self.image_path.write_bytes(binary_data)
        elif pil_image is not None:
            pil_image.save(self.image_path)
        else:
            raise ValueError("At least an image path, binary data or PIL image"
                             " object is needed")
        self.update(**kwds)
        self.save()

    def __getattr__(self, attr):
        if attr == 'image':
            from PIL import Image
            self.image = Image.open(self.image_path)
            return self.image
