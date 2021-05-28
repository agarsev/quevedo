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
        #: Number which identifies this annotation in its subset.
        self.id = path.stem
        #: Path to the json annotation file. It is the id plus `json` extension.
        self.json_path = path.with_suffix('.json')
        #: Path to the source image for the annotation. It is the id plus `png` extension.
        self.image_path = path.with_suffix('.png')
        #: Dictionary of metadata annotations.
        self.meta = {}
        #: Train/test split to which the annotation belongs.
        self.set = 'train'
        if self.json_path.exists():
            self.update(**json.loads(self.json_path.read_text()))

    def update(self, *, meta=None, set=None, **kwds):
        '''Update the content of the annotation.

        This method should be overriden by the specific annotation classes to
        add their specific annotation information.

        Args:
            meta: dictionary of metadata values to set.
            set: train/test split to which the annotation will belong.
        '''
        if meta:
            self.meta = meta
        if set:
            self.set = set

    def to_dict(self):
        '''Get the annotation data as a dictionary.'''
        return {'meta': self.meta, 'set': self.set}

    def save(self):
        '''Persist the information to the filesystem.'''
        self.json_path.write_text(json.dumps(self.to_dict()))

    def create_from(self, *, image_path=None, binary_data=None,
                    pil_image=None, **kwds):
        '''Initialize an annotation with some source image data.

        One of `image_path`, `binary_data` or `pil_image` must be provided.
        Other arguments will be passed to
        [`update`](#quevedo.annotation.annotation.Annotation.update) so metadata
        or tags can also be set.

        The annotation will be persisted with a call to `save` too.

        Args:
            image_path: path to an image in the filesystem to use as image for
                this annotation. The image will be **copied** into the dataset.
            binary_data: bytes array which encodes the source image. The
                contents will be dumped to the appropriate image file in the
                dataset.
            pil_image: [PIL.Image.Image] object to be stored as image file for
                this annotation in the dataset.
        '''
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

    @property
    def image(self):
        '''PIL.Image.Image: image data for this annotation.'''
        if not hasattr(self, '_image_data'):
            from PIL import Image
            self._image_data = Image.open(self.image_path)
        return self._image_data
