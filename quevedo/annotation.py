# 2020-11-11 Antonio F. G. Sevilla <afgs@ucm.es>

from enum import Enum
import json
from pathlib import Path
from shutil import copyfile

Target = Enum('AnnotationTarget', 'TRAN SYMB')


class Annotation:
    '''Class representing a single annotation of either a transcription of a
    sign or signs in the dataset or an isolated symbol.'''

    def __init__(self, path, target=Target.TRAN):
        path = Path(path)
        self.id = path.stem
        self.target = target
        self._json = path.with_suffix('.json')
        self.image = path.with_suffix('.png')
        self._txt = path.with_suffix('.txt')

    def _init_json(self, meta={}, **more):
        d = {"set": "train", "meta": meta, **more }
        if self.target == Target.TRAN:
            d['symbols'] = []
        elif self.target == Target.SYMB:
            d['tags'] = []
        self.anot = d
        self.save()

    def create_from(self, *, image_path=None, binary_data=None,
                    pil_image=None, **more):
        if image_path is not None:
            copyfile(image_path, self.image)
            self._init_json(meta={
                'filename': image_path.stem,
            }, **more)
        elif binary_data is not None:
            self.image.write_bytes(binary_data)
            self._init_json(**more)
        elif pil_image is not None:
            pil_image.save(self.image)
            self._init_json(**more)

    def save(self):
        self._json.write_text(json.dumps(self.anot))

    def __getattr__(self, attr):
        if attr == 'anot':
            if not self._json.exists():
                self._init_json()
            self.anot = json.loads(self._json.read_text())
            return self.anot
