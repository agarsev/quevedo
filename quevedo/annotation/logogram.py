# 2021-04-29 Antonio F. G. Sevrlla <afgs@ucm.es>
# Licensed under the Open Software License version 3.0

from .annotation import Annotation, Target
from .grapheme import Grapheme


class Logogram(Annotation):
    '''Annotation for a logogram, with its contained graphemes.'''

    target = Target.LOGO

    def __init__(self, *args, **kwargs):
        #: annotated tags for this logogram.
        self.tags = {}  # type: dict[str,str]
        #: list of [bound graphemes](#quevedoannotationlogogramboundgrapheme) found within this logogram.
        self.graphemes = []  # type: list[BoundGrapheme]
        #: list of [edges](#quevedoannotationlogogramedge) found within this logogram.
        self.edges = []  # type: list[Edge]
        super().__init__(*args, **kwargs)

    def update(self, *, tags=None, graphemes=None, edges=None, **kwds):
        '''Extends base
        [`update`](#quevedo.annotation.annotation.Annotation.update), other
        arguments will be passed through.

        Args:
            tags: new tags for this logogram (replaces all).
            graphemes: either a list of Graphemes, BoundGraphemes, or dicts with
                the keys necessary to initialize a
                [BoundGrapheme](quevedoannotationlogogramboundgrapheme).
            edges: either a list of Edges, or dicts with the keys necessary to
                initialize an [Edge](quevedoannotationlogogramedge). In this
                case, start and end should be the indices of the boundgraphemes
                in the graphemes list.
        '''
        super().update(**kwds)
        if tags is not None:
            self.tags = {k: t for k, t in tags.items()
                         if t is not None and t != ''}
        if graphemes is not None:
            self.graphemes = [BoundGrapheme(self, **g)
                              if isinstance(g, dict) else g
                              for g in graphemes]
        if edges is not None:
            self.edges = [Edge(self.graphemes[e['start']],
                               self.graphemes[e['end']],
                               e['tags'])
                          if isinstance(e, dict) else e
                          for e in edges]

    def to_dict(self):
        return {
            **super().to_dict(),
            'tags': {k: t for k, t in self.tags.items()
                     if t is not None and t != ''},
            'graphemes': [g.to_dict() for g in self.graphemes],
            'edges': [{
                'start': self.graphemes.index(e.start),
                'end': self.graphemes.index(e.end),
                'tags': e.tags
            } for e in self.edges]
        }


class BoundGrapheme(Grapheme):
    '''A grapheme which is not isolated, but rather forms part of a logogram.

    To promote this bound grapheme to an isolated grapheme with its own
    annotation, create a grapheme object using
    [`create_from`](#quevedo.annotation.annotation.Annotation.create_from),
    passing this object's `image` to the argument `pil_image`.
    '''

    def __init__(self, logogram, box=[0, 0, 0, 0], *args, **kwargs):
        #: Logogram where this grapheme is found.
        self.logogram = logogram
        self._box = box
        super().__init__(*args, **kwargs)

    def to_dict(self):
        return {**super().to_dict(), 'box': self.box}

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
        return self._image_data

    @property
    def box(self):
        '''list[float]: Bounding box coordinates (x, y, w, h) of this grapheme
        within the logogram.

        - (x, y): coordinates of the **center**.
        - (w, h): width and height.

        Values are relative to the logogram size, in the range `[0, 1]`.'''
        return self._box

    @box.setter
    def box(self, coords):
        self._box = coords
        if hasattr(self, '_image_data'):
            del self._image_data

    def outbound(self):
        '''Generator[Edge,None,None]: edges in the logogram emanating from this
        grapheme.'''
        return (e for e in self.logogram.edges if e.start == self)

    def inbound(self):
        '''Generator[Edge,None,None]: edges in the logogram ending in this
        grapheme.'''
        return (e for e in self.logogram.edges if e.end == self)


class Edge:
    '''An edge between graphemes in a logogram.

    Edges are used to connect two graphemes, and can be used to define the
    dependency or function between them. The edges and graphemes of a logogram
    form a directed graph. The tags for an edge are a dictionary with keys in
    the dataset's `e_tags` field.'''

    def __init__(self, start: BoundGrapheme, end: BoundGrapheme, tags: dict = {}):
        #: [bound grapheme](#quevedoannotationlogogramboundgrapheme) origin of the edge
        self.start = start  # type: BoundGrapheme
        #: [bound grapheme](#quevedoannotationlogogramboundgrapheme) end of the edge
        self.end = end  # type: BoundGrapheme
        #: annotated tags for this edge.
        self.tags = tags  # type: dict[str,str]
