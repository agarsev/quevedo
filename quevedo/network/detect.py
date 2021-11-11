# 2021-04-21 Antonio F. G. Sevilla <afgs@ucm.es>
# Licensed under the Open Software License version 3.0

import json
from pathlib import Path
from PIL import Image
from string import Template

from .network import Network
from quevedo.annotation import Target
from quevedo.annotation.logogram import Logogram, BoundGrapheme


class DetectNet(Network):
    '''A neural network for performing grapheme detection within logograms.'''

    target = Target.LOGO
    names_file_name = 'names'  # Darknet is not very consistent
    network_type = 'detector'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        #: IOU threshold for matching a prediction to a grapheme during test
        self.threshold = self.config.get('threshold', 0.2)

    def _update_tag_set(self, tag_set, annotation):
        try:
            tag_set.update(set(self.get_tag(g.tags)
                               for g in annotation.graphemes))
        except KeyError:
            raise KeyError("Error getting annotations for logogram {} ({})".format(
                annotation.id, json.dumps(annotation.to_dict())))

    def _prepare_annotation(self, annotation, num, tag_set):
        # For YOLO, we write an adjacent txt file with the bounding boxes and
        # the class (its index)
        link_name = "{}.png".format(num)
        (self.train_path / link_name).with_suffix(".txt").write_text(
            "".join("{} {} {} {} {}\n".format(
                tag_set.index(self.get_tag(g.tags)),
                *g.box) for g in annotation.graphemes))
        return link_name

    def _get_net_config(self, num_classes):
        template = Template((Path(__file__).parent.parent /
                             'darknet/yolo.cfg').read_text())
        config = self.config
        augment = self.config.get('augment', {})

        num_max_batches = config.get('max_batches',
            num_classes * 1000)

        return template.substitute(
            height=config.get('height', 416),  # Important! multiple of 32
            width=config.get('width', 416),    # Important! multiple of 32
            flip=augment.get('flip', 0),
            angle=augment.get('angle', 0),
            exposure=augment.get('exposure', 0),
            num_classes=num_classes,
            num_filters=((num_classes + 5) * 3),
            num_max_batches=num_max_batches,
            num_steps_1=int(num_max_batches * 80 / 100),
            num_steps_2=int(num_max_batches * 90 / 100))

    def predict(self, image):

        if not isinstance(image, Image.Image):
            image = Image.open(image)

        def clamp(val, minim, maxim):
            return min(maxim, max(minim, val))

        def make_bbox(im_width, im_height, x, y, w, h):
            x = clamp(x / im_width, 0, 1)
            y = clamp(y / im_height, 0, 1)
            w = clamp(w / im_width, 0, 1)
            h = clamp(h / im_height, 0, 1)
            return [x, y, w, h]

        width, height = image.size
        ret = Logogram(image=image)
        ret.graphemes = [BoundGrapheme(logogram=ret,
            meta={'confidence': c},
            tags=self.prediction_to_tag(self.tag_map[s]),
            box=make_bbox(width, height, *b))
            for (s, c, b) in self._darknet.detect(image)]
        return ret

    def test(self, annotation, stats):
        prediction = self.predict(annotation.image_path)
        image = annotation.image_path.relative_to(self.dataset.path)
        for (pred, truth, iou) in match(prediction.graphemes, annotation.graphemes, self.threshold):
            if truth is not None:
                truth = self.get_tag(truth.tags)
            confidence = 0
            if pred is not None:
                confidence = pred.meta.get('confidence', 0)
                pred = self.get_tag(pred.tags)
            stats.register(prediction=pred, truth=truth,
                image=image, confidence=confidence, iou=iou)

    def auto_annotate(self, a):
        predicted = self.predict(a.image)
        a.update(graphemes=predicted.graphemes)


# Utilities for YOLO

def safe_divide(a, b):
    if a == 0:
        return 0
    elif b == 0:
        return 1
    else:
        return a / b


def box(xc, yc, w, h):
    return {
        'l': float(xc) - float(w) / 2,
        'r': float(xc) + float(w) / 2,
        'b': float(yc) - float(h) / 2,
        't': float(yc) + float(h) / 2,
        'w': float(w),
        'h': float(h)
    }


def calc_iou(a, b):
    '''Intersection over union for boxes in x, y, w, h format'''
    a = box(*a)
    b = box(*b)
    # Intersection
    il = max(a['l'], b['l'])
    ir = min(a['r'], b['r'])
    ix = ir - il if ir > il else 0
    ib = max(a['b'], b['b'])
    it = min(a['t'], b['t'])
    iy = it - ib if it > ib else 0
    i = ix * iy
    # Sum (union = sum - inters)
    s = a['w'] * a['h'] + b['w'] * b['h']
    return safe_divide(i, (s - i))


def match(x, y, threshold=0.2):
    '''Match two lists of graphemes according to best box fit.

    Receives two grapheme lists and returns a list of 3-tuples, where the first
    element is from the first list, the second element from the second list, and
    the third element is the IOU measure between their boxes. Each grapheme of
    either list will appear only once. If the IOU between elements is less than
    the threshold, it won't be considered a match.  Unmatched elements will
    still appear in the return list, but their counterpart object in the tuple
    will be `None`.'''
    x = [a for a in x]
    nx = len(x)
    y = [b for b in y]
    ny = len(y)
    matches = [(i, j, calc_iou(x[i].box, y[j].box))
               for i in range(nx)
               for j in range(ny)]
    matches.sort(reverse=True, key=lambda m: m[2])
    ret = []
    while len(matches) > 0 and nx > 0 and ny > 0:
        i, j, iou = matches.pop(0)
        if x[i] is None or y[j] is None:
            continue
        if iou <= threshold:
            break
        ret.append((x[i], y[j], iou))
        x[i] = None
        nx -= 1
        y[j] = None
        ny -= 1
    ret += ((a, None, 0) for a in x if a is not None)
    ret += ((None, b, 0) for b in y if b is not None)
    return ret
