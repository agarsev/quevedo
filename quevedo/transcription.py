# 2020-11-11 Antonio F. G. Sevilla <afgs@ucm.es>

import json
from pathlib import Path
from shutil import copyfile


class Transcription:
    '''Class representing a single transcription of a sign or signs in the
    dataset.'''

    def __init__(self, path):
        path = Path(path)
        self._json = path.with_suffix('.json')
        self.image = path.with_suffix('.png')
        self._txt = path.with_suffix('.txt')

    def _init_json(self, meanings=[]):
        self._json.write_text(json.dumps({
            "meanings": meanings,
            "symbols": [],
            "set": "train",
        }))

    def create_from(self, image):
        copyfile(image, self.image)
        self._init_json(meanings=[image.stem])

    def save(self):
        self._json.write_text(json.dumps(self.anot))

    def __getattr__(self, attr):
        if attr == 'anot':
            if not self._json.exists():
                self._init_json()
            self.anot = json.loads(self._json.read_text())
            return self.anot
