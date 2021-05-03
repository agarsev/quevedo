# 2021-04-29 Antonio F. G. Sevilla <afgs@ucm.es>

from .annotation import Annotation, Target


class Logogram(Annotation):

    target = Target.LOGO

    def __init__(self, *args):
        self.graphemes = []  # type: list[BoundGrapheme]
        super().__init__(*args)

    def update(self, *, graphemes=None, **kwds):
        super().update(**kwds)
        if graphemes is not None:
            self.graphemes = [BoundGrapheme(self, **g) for g in graphemes]

    def to_dict(self):
        return {
            **super().to_dict(),
            'graphemes': [g.to_dict() for g in self.graphemes]
        }


class BoundGrapheme():

    def __init__(self, logogram, box=[0, 0, 0, 0], tags=[]):
        self.logogram = logogram
        self.box = box  # type: list[float]
        self.tags = tags  # type: list[str]

    def to_dict(self):
        return {'box': self.box, 'tags': self.tags}

    def __getattr__(self, attr):
        if attr == 'image':
            img = self.logogram.image
            width, height = img.size
            w = float(self.box[2]) * width
            h = float(self.box[3]) * height
            l = float(self.box[0]) * width - (w / 2)
            u = float(self.box[1]) * height - (h / 2)
            self.image = img.crop((l, u, l + w, u + h))
            return self.image
