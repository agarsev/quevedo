# 2021-04-29 Antonio F. G. Sevilla <afgs@ucm.es>

from .annotation import Annotation, Target


class Grapheme(Annotation):

    target = Target.GRAPH

    def __init__(self, *args):
        self.tags = []
        super().__init__(*args)

    def update(self, *, tags=None, **kwds):
        super().update(**kwds)
        if tags is not None:
            self.tags = tags

    def to_dict(self):
        return {
            **super().to_dict(),
            'tags': self.tags
        }
