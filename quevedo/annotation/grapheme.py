# 2021-04-29 Antonio F. G. Sevilla <afgs@ucm.es>
# Licensed under the Open Software License version 3.0

from .annotation import Annotation, Target


class Grapheme(Annotation):
    '''Annotation for an isolated grapheme.'''

    target = Target.GRAPH

    def __init__(self, *args):
        #: list of values for this grapheme's tags in the dataset's `tag_schema`.
        self.tags = []
        super().__init__(*args)

    def update(self, *, tags=None, **kwds):
        '''Extends base
        [`update`](#quevedo.annotation.annotation.Annotation.update), other
        arguments will be passed through.

        Args:
            tags: new tags for this grapheme (replaces all).
        '''
        super().update(**kwds)
        if tags is not None:
            self.tags = tags

    def to_dict(self):
        return {
            **super().to_dict(),
            'tags': self.tags
        }
