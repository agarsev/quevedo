# 2021-04-21 Antonio F. G. Sevilla <afgs@ucm.es>

from pathlib import Path
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
