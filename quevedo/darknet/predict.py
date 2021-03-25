# 2020-05-04 Antonio F. G. Sevilla <afgs@ucm.es>

import os
from PIL import Image
import sys

from quevedo.darknet.library import init

# Functions that perform the actual predictions after loading the neural net
perform_detect = None
perform_classify = None


def cstr(s):
    return str(s).encode('utf8')


def clamp(val, minim, maxim):
    return min(maxim, max(minim, val))


def make_bbox(im_width, im_height, x, y, w, h):
    x = clamp(x / im_width, 0, 1)
    y = clamp(y / im_height, 0, 1)
    w = clamp(w / im_width, 0, 1)
    h = clamp(h / im_height, 0, 1)
    return [x, y, w, h]


# Only way to suppress usual darknet output as much as possible
class DarknetShutup(object):

    def __enter__(self):
        self.stderr_fileno = sys.stderr.fileno()
        self.stderr_save = os.dup(self.stderr_fileno)
        self.stdout_fileno = sys.stdout.fileno()
        self.stdout_save = os.dup(self.stdout_fileno)
        self.devnull = open(os.devnull, 'w')
        devnull_fn = self.devnull.fileno()
        os.dup2(devnull_fn, self.stderr_fileno)
        os.dup2(devnull_fn, self.stdout_fileno)

    def __exit__(self, type, value, traceback):
        self.devnull.close()
        os.dup2(self.stderr_save, self.stderr_fileno)
        os.dup2(self.stdout_save, self.stdout_fileno)
        os.close(self.stderr_save)
        os.close(self.stdout_save)


def init_darknet(dataset, experiment):
    '''Loads the trained neural network. Must be called before predict.'''

    global perform_detect, perform_classify

    if not (experiment.path / 'darknet.cfg').exists():
        raise SystemExit("Neural network has not been trained")

    darknet_data = (experiment.path / 'darknet.data').resolve()
    darknet_cfg = (experiment.path / 'darknet.cfg').resolve()
    weights = (experiment.path / 'darknet_final.weights').resolve()

    if not weights.exists():
        raise SystemExit("Neural network has not been trained")

    with DarknetShutup():
        perform_detect, perform_classify = init(
            libraryPath=cstr(dataset.config['darknet']['library']),
            configPath=cstr(darknet_cfg),
            weightPath=cstr(weights),
            metaPath=cstr(darknet_data))


def predict(image_path, experiment):
    '''Get graphemes in an image using the trained neural network (which must have
    been loaded using init_darknet)'''

    if experiment.config['task'] == 'detect':
        width, height = Image.open(image_path).size
        return [{
            'name': s,
            'confidence': c,
            'box': make_bbox(width, height, *b)
        } for (s, c, b) in perform_detect(cstr(image_path))]
    elif experiment.config['task'] == 'classify':
        return [{
            'tag': tag.decode('utf8'),
            'confidence': conf
        } for (tag, conf) in perform_classify(cstr(image_path))]
