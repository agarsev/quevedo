# 2021-04-29 Antonio F. G. Sevilla <afgs@ucm.es>
# Licensed under the Open Software License version 3.0

from .annotation import Annotation, Target


class Logogram(Annotation):
    '''Annotation for a logogram, with its contained graphemes.'''

    target = Target.LOGO

    def __init__(self, *args):
        #: list of [bound graphemes](#quevedoannotationlogogramboundgrapheme) found within this logogram.
        self.graphemes = []  # type: list[BoundGrapheme]
        super().__init__(*args)

    def update(self, *, graphemes=None, **kwds):
        '''Extends base
        [`update`](#quevedo.annotation.annotation.Annotation.update), other
        arguments will be passed through.

        Args:
            graphemes: a list of dicts with the grapheme information for this logogram.
                The dicts must have the keys necessary to initialize a
                [BoundGrapheme](quevedoannotationlogogramboundgrapheme).
        '''
        super().update(**kwds)
        if graphemes is not None:
            self.graphemes = [BoundGrapheme(self, **g) for g in graphemes]

    def to_dict(self):
        return {
            **super().to_dict(),
            'graphemes': [g.to_dict() for g in self.graphemes]
        }


class BoundGrapheme():
    '''A grapheme which is not isolated, but rather forms part of a logogram.

    To promote this bound grapheme to an isolated grapheme with its own
    annotation, create a grapheme object using
    [`create_from`](#quevedo.annotation.annotation.Annotation.create_from),
    passing this object's `image` to the argument `pil_image`.
    '''

    def __init__(self, logogram, box=[0, 0, 0, 0], tags=[]):
        #: Logogram where this grapheme is found.
        self.logogram = logogram
        #: Coordinates (x, y, w, h) of this grapheme's bounding box within the logogram. x and y are the coordinates of the **center**. Values are relative to the logogram size, in the range `[0, 1]`.
        self.box = box  # type: list[float]
        #: list of values for this grapheme's tags in the dataset's `tag_schema`.
        self.tags = tags  # type: list[str]

    def to_dict(self):
        return {'box': self.box, 'tags': self.tags}

    @property
    def image(self):
        '''PIL.Image.Image: image data for only this grapheme, cropped out of
        the parent logogram's image.'''
        if not hasattr(self, '_image_data'):
            img = self.logogram.image
            width, height = img.size
            w = float(self.box[2]) * width
            h = float(self.box[3]) * height
            l = float(self.box[0]) * width - (w / 2)
            u = float(self.box[1]) * height - (h / 2)
            self._image_data = img.crop((l, u, l + w, u + h))
        return self.image
