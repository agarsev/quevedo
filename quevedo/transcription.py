# 2020-11-11 Antonio F. G. Sevilla <afgs@ucm.es>

import json
from pathlib import Path
from shutil import copyfile


class Transcription:
    '''Class representing a single transcription of a sign or signs in the
    dataset.'''

    def __init__(self, path):
        path = Path(path)
        self.id = path.stem
        self._json = path.with_suffix('.json')
        self.image = path.with_suffix('.png')
        self._txt = path.with_suffix('.txt')

    def _init_json(self, notes=''):
        self._json.write_text(json.dumps({
            "notes": notes,
            "symbols": [],
            "set": "train",
        }))

    def create_from(self, image=None, binary_data=None):
        if image is not None:
            copyfile(image, self.image)
            self._init_json(notes=image.stem)
        elif binary_data is not None:
            self.image.write_bytes(binary_data)
            self._init_json()

    def save(self):
        self._json.write_text(json.dumps(self.anot))

    def __getattr__(self, attr):
        if attr == 'anot':
            if not self._json.exists():
                self._init_json()
            self.anot = json.loads(self._json.read_text())
            return self.anot
