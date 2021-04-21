# 2021-04-21 Antonio F. G. Sevilla <afgs@ucm.es>

from pathlib import Path
from PIL import Image
from string import Template

from .network import Network
from quevedo.annotation import Target


class DetectNet(Network):
    '''A neural network for performing grapheme detection within logograms.'''

    def __init__(self, *kwds):
        super().__init__(*kwds)
        self.target = Target.LOGO
        self.names_file_name = 'names'  # Darknet is not very consistent
        self.network_type = 'detector'

    def update_tag_set(self, tag_set, annotation):
        tag_set.update(set(self.get_tag(s['tags'])
                           for s in annotation.anot['graphemes']))

    def prepare_annotation(self, annotation, num, tag_set):
        # For YOLO, we write an adjacent txt file with the bounding boxes and
        # the class (its index)
        link_name = "{}.png".format(num)
        (self.train_path / link_name).with_suffix(".txt").write_text(
            "".join("{} {} {} {} {}\n".format(
                tag_set.index(self.get_tag(s['tags'])),
                *s['box']) for s in annotation.anot['graphemes']))
        return link_name

    def get_net_config(self, num_classes):
        num_max_batches = num_classes * 200 # 2000, 200 only for testing
        template = Template((Path(__file__).parent.parent /
                             'darknet/yolo.cfg').read_text())
        return template.substitute(
            num_classes=num_classes,
            num_filters=((num_classes + 5) * 3),
            num_max_batches=num_max_batches,
            num_steps_1=int(num_max_batches * 80 / 100),
            num_steps_2=int(num_max_batches * 90 / 100))

    def predict(self, image_path):

        if self._darknet is None:
            self.load()

        def clamp(val, minim, maxim):
            return min(maxim, max(minim, val))

        def make_bbox(im_width, im_height, x, y, w, h):
            x = clamp(x / im_width, 0, 1)
            y = clamp(y / im_height, 0, 1)
            w = clamp(w / im_width, 0, 1)
            h = clamp(h / im_height, 0, 1)
            return [x, y, w, h]

        width, height = Image.open(image_path).size
        return [{
            'name': self.tag_map[s],
            'confidence': c,
            'box': make_bbox(width, height, *b)
        } for (s, c, b) in self._darknet.detect(image_path)]
