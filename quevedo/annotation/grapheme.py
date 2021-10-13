# 2021-04-29 Antonio F. G. Sevilla <afgs@ucm.es>
# Licensed under the Open Software License version 3.0

from .annotation import Annotation, Target


class Grapheme(Annotation):
    '''Annotation for an isolated grapheme.'''

    target = Target.GRAPH

    def __init__(self, *args, **kwargs):
        #: annotated tags for this grapheme.
        self.tags = {}  # type: dict[str,str]
        super().__init__(*args, **kwargs)

    def update(self, *, tags=None, **kwds):
        '''Extends base
        [`update`](#quevedo.annotation.annotation.Annotation.update), other
        arguments will be passed through.

        Args:
            tags: new tags for this grapheme (replaces all).
        '''
        super().update(**kwds)
        if tags is not None:
            self.tags = {k: t for k, t in tags.items()
                         if t is not None and t != ''}

    def to_dict(self):
        return {
            **super().to_dict(),
            'tags': {k: t for k, t in self.tags.items()
                     if t is not None and t != ''}
        }
