# 2020-05-04 Antonio F. G. Sevilla <afgs@ucm.es>

from ctypes import c_char_p
from math import ceil, floor
from PIL import Image

from swrec.darknet.library import init, detect

net = None
meta = None

def cstr (s):
    return c_char_p(str(s).encode('utf8'))

def clamp (val, minim, maxim):
    return min(maxim, max(minim, val))

def make_bbox(im_width, im_height, x, y, w, h):
    x = clamp(x/im_width, 0, 1)
    y = clamp(y/im_height, 0, 1)
    w = clamp(w/im_width, 0, 1)
    h = clamp(h/im_height, 0, 1)
    return [x, y, w, h]

def init_darknet (dataset):
    '''Loads the trained neural network. Must be called before predict.'''

    global net, meta

    dn_dir = dataset.path / 'darknet'
    if not dn_dir.exists():
        raise SystemExit("Neural network has not been trained")
    
    darknet_data = (dn_dir / 'darknet.data').resolve()
    darknet_cfg = (dn_dir / 'darknet.cfg').resolve()
    weights = (dataset.path / 'weights' / 'darknet_final.weights').resolve()

    if not weights.exists():
        raise SystemExit("Neural network has not been trained")

    load_net, load_meta = init(dataset.info['darknet']['library'])
    net = load_net(cstr(darknet_cfg), cstr(weights), 0)
    meta = load_meta(cstr(darknet_data))

def predict (image_path):
    '''Get symbols in an image using the trained neural network (which must have
    been loaded using init_darknet)'''

    width, height = Image.open(image_path).size
    return [{
        'name': s.decode('utf8'),
        'confidence': c,
        'bbox': make_bbox(width, height, *b)
    } for (s, c, b) in detect(net, meta, cstr(image_path))]
