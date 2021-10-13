# 2021-04-21 Antonio F. G. Sevilla <afgs@ucm.es>
# Licensed under the Open Software License version 3.0

from pathlib import Path
from string import Template

from .network import Network
from quevedo.annotation import Target, Grapheme


class ClassifyNet(Network):
    '''A neural network for classifying graphemes.'''

    target = Target.GRAPH
    names_file_name = 'labels'  # Darknet is not very consistent
    network_type = 'classifier'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        filt = self.config.get('filter', None)
        #: Confidence threshold for returning a classification instead of None
        self.threshold = self.config.get('threshold', 0.2)
        if filt:
            try:
                crit = filt['criterion']
                if 'include' in filt:
                    tags = set(filt['include'])
                    self._filter = lambda a: a.tags.get(crit) in tags
                else:
                    tags = set(filt['exclude'])
                    self._filter = lambda a: a.tags.get(crit) not in tags
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
        template = Template((Path(__file__).parent.parent /
                             'darknet/alexnet.cfg').read_text())
        config = self.config
        augment = config.get('augment', {})

        num_max_batches = config.get('max_batches',
                    1000 + num_classes * 20)

        return template.substitute(
            flip=augment.get('flip', 0),
            angle=augment.get('angle', 0),
            exposure=augment.get('exposure', 0),
            aspect=augment.get('aspect', 0),
            num_max_batches=num_max_batches,

            num_classes=num_classes,
            num_connected=num_classes * 10)

    def predict(self, image):
        return [Grapheme(
            tags=self.prediction_to_tag(
                self.tag_map[tag.decode('utf8')]),
            meta={'confidence': conf})
                for (tag, conf) in self._darknet.classify(image)]

    def test(self, annotation, stats):
        true_tag = self.get_tag(annotation.tags)
        if true_tag is None:  # Should we allow empty images?
            return
        predictions = self.predict(annotation.image_path)
        best_tag = None
        confidence = 0
        if len(predictions) > 0:
            best = predictions[0]
            if best.meta['confidence'] >= self.threshold:
                best_tag = self.get_tag(best.tags)
                confidence = best.meta['confidence']
        stats.register(truth=true_tag, prediction=best_tag,
            image=annotation.image_path.relative_to(self.dataset.path),
            confidence=confidence)

    def auto_annotate(self, a):
        preds = self.predict(a.image)
        if len(preds) > 0:
            a.tags.update(preds[0].tags)
