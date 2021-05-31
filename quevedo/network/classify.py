# 2021-04-21 Antonio F. G. Sevilla <afgs@ucm.es>
# Licensed under the Open Software License version 3.0

from pathlib import Path
from string import Template

from .network import Network
from quevedo.annotation import Target


class ClassifyNet(Network):
    '''A neural network for classifying graphemes.'''

    target = Target.GRAPH
    names_file_name = 'labels'  # Darknet is not very consistent
    network_type = 'classifier'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        filt = self.config.get('filter', None)
        if filt:
            try:
                tag_schema = self.dataset.config['tag_schema']
                crit = tag_schema.index(filt['criterion'])
                if 'include' in filt:
                    tags = set(filt['include'])
                    self._filter = lambda a: a.tags[crit] in tags
                else:
                    tags = set(filt['exclude'])
                    self._filter = lambda a: a.tags[crit] not in tags
            except KeyError:
                raise RuntimeError("Incorrect filter config for network '{}'".format(
                    self.name)) from None

    def _update_tag_set(self, tag_set, annotation):
        tag = self.get_tag(annotation.tags)
        if tag is not None:
            tag_set.add(tag)

    def _prepare_annotation(self, annotation, num, tag_set):
        # For CNN, no need to write a label file, just put the label in the
        # filename
        tag = self.get_tag(annotation.tags)
        if tag is None:
            return None
        return "{}_{}.png".format(self.tag_map[tag], num)

    def _get_net_config(self, num_classes):
        # FIXME: Choose these params better and allow user customisation
        template = Template((Path(__file__).parent.parent /
                             'darknet/alexnet.cfg').read_text())
        augment = self.config.get('augment', {})
        return template.substitute(
            flip=augment.get('flip', 0),
            angle=augment.get('angle', 0),
            exposure=augment.get('exposure', 0),
            aspect=augment.get('aspect', 0),
            num_classes=num_classes,
            num_max_batches=num_classes * 10,  # maybe?
            num_connected=num_classes * 10)

    def predict(self, image):
        return [{
            'tag': self.tag_map[tag.decode('utf8')],
            'confidence': conf
        } for (tag, conf) in self._darknet.classify(image)]

    def test(self, annotation, stats):
        true_tag = self.get_tag(annotation.tags)
        if true_tag is None:  # Should we allow empty images?
            return
        predictions = self.predict(annotation.image_path)
        best = predictions[0]
        # FIXME thresholds should be configuration, in detect too
        stats.register(best['tag'] if best['confidence'] >= 0.5 else None,
                       true_tag)

    def auto_annotate(self, a):
        preds = self.predict(a.image)
        self.prediction_to_tag(a.tags, preds[0]['tag'])
