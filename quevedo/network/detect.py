# 2021-04-21 Antonio F. G. Sevilla <afgs@ucm.es>
# Licensed under the Open Software License version 3.0

import json
from pathlib import Path
from PIL import Image
from string import Template

from .network import Network
from quevedo.annotation import Target


class DetectNet(Network):
    '''A neural network for performing grapheme detection within logograms.'''

    target = Target.LOGO
    names_file_name = 'names'  # Darknet is not very consistent
    network_type = 'detector'

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
        num_max_batches = num_classes * 400  # 2000, 400 only for testing
        template = Template((Path(__file__).parent.parent /
                             'darknet/yolo.cfg').read_text())
        augment = self.config.get('augment', {})
        return template.substitute(
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

        return [{
            'name': self.tag_map[s],
            'confidence': c,
            'box': make_bbox(width, height, *b)
        } for (s, c, b) in self._darknet.detect(image)]

    def test(self, annotation, stats):
        predictions = self.predict(annotation.image_path)
        for g in annotation.graphemes:
            tag = self.get_tag(g.tags)
            if tag is None:
                continue
            logo = {'box': g.box, 'name': tag}
            if len(predictions) > 0:
                similarities = sorted(((box_similarity(p, logo), i) for (i, p) in
                                      enumerate(predictions)), reverse=True)
                (sim, idx) = similarities[0]
                if sim > 0.7:
                    predictions.pop(idx)
                    # Tag equality is checked in the similarity computation
                    stats.register(tag, tag)
                    continue
            stats.register(None, tag)
        # Unassigned predictions are false positives
        for pred in predictions:
            stats.register(pred['name'], None)

    def auto_annotate(self, a):
        graphemes = []
        for pred in self.predict(a.image):
            g = {'box': pred['box'], 'tags': []}
            self.prediction_to_tag(g['tags'], pred['name'])
            graphemes.append(g)
        a.update(graphemes=graphemes)


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


def box_similarity(a, b):
    '''Similarity of grapheme boxes.'''
    return iou(a['box'], b['box']) if (a['name'] == b['name']) else 0


def iou(a, b):
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
