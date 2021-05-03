# 2021-04-21 Antonio F. G. Sevilla <afgs@ucm.es>

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
                    self.filter = lambda a: a.tags[crit] in tags
                else:
                    tags = set(filt['exclude'])
                    self.filter = lambda a: a.tags[crit] not in tags
            except KeyError:
                raise RuntimeError("Incorrect filter config for network '{}'".format(
                    self.name)) from None

    def update_tag_set(self, tag_set, annotation):
        tag = self.get_tag(annotation.tags)
        if tag is not None:
            tag_set.add(tag)

    def prepare_annotation(self, annotation, num, tag_set):
        # For CNN, no need to write a label file, just put the label in the
        # filename
        tag = self.get_tag(annotation.tags)
        if tag is None:
            return None
        return "{}_{}.png".format(self.tag_map[tag], num)

    def get_net_config(self, num_classes):
        # TODO: Read somewhere how to choose these params
        template = Template((Path(__file__).parent.parent /
                             'darknet/alexnet.cfg').read_text())
        return template.substitute(
            num_classes=num_classes,
            num_max_batches=num_classes * 10,  # maybe?
            num_connected=num_classes * 10)

    def predict(self, image):
        if self._darknet is None:
            self.load()
        return [{
            'tag': self.tag_map[tag.decode('utf8')],
            'confidence': conf
        } for (tag, conf) in self._darknet.classify(image)]

    def test(self, annotation, stats):
        true_tag = self.get_tag(annotation.tags)
        if true_tag is None:
            return
        predictions = self.predict(annotation.image_path)
        best = predictions[0]
        stats.add(true_tag)
        # TODO thresholds should be configuration, in detect too
        if best['confidence'] < 0.5:  # no prediction
            if true_tag != '':
                stats.false_negatives[true_tag] += 1
        else:
            if true_tag == best['tag']:
                stats.true_positives[true_tag] += 1
            else:
                stats.false_positives[best['tag']] += 1

    def auto_annotate(self, a):
        preds = self.predict(a.image)
        self.prediction_to_tag(a.tags, preds[0]['tag'])
