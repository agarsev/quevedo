# 2021-04-21 Antonio F. G. Sevilla <afgs@ucm.es>

from pathlib import Path
from string import Template

from .network import Network
from quevedo.annotation import Target


class ClassifyNet(Network):
    '''A neural network for classifying graphemes.'''

    def __init__(self, *kwds):
        super().__init__(*kwds)
        self.target = Target.GRAPH
        self.names_file_name = 'labels'  # Darknet is not very consistent
        self.network_type = 'classifier'

    def update_tag_set(self, tag_set, annotation):
        tag = self.get_tag(annotation.anot['tags'])
        if tag is not None:
            tag_set.add(tag)

    def prepare_annotation(self, annotation, num, tag_set):
        # For CNN, no need to write a label file, just put the label in the
        # filename
        tag = self.get_tag(annotation.anot['tags'])
        if tag is None:
            return None
        return "{}_{}.png".format(self.tag_map[tag], num)

    def get_net_config(self, num_classes):
        # TODO: Read somewhere how to choose these params
        template = Template((Path(__file__).parent.parent /
                             'darknet/alexnet.cfg').read_text())
        return template.substitute(
            num_classes=num_classes,
            num_max_batches=num_classes * 50,  # maybe?
            num_connected=num_classes * 10)

    def predict(self, image_path):

        if self._darknet is None:
            self.load()

        return [{
            'tag': self.tag_map[tag.decode('utf8')],
            'confidence': conf
        } for (tag, conf) in self._darknet.classify(image_path)]
