# 2021-11-10 Antonio F. G. Sevilla <afgs@ucm.es>
# Licensed under the Open Software License version 3.0

import click
import json

from quevedo.annotation import Target, Grapheme, Logogram
from quevedo.network.detect import match


@click.command('predict')
@click.option('--image', '-i', type=click.Path(exists=True),
              required=True, help="Image to predict")
@click.pass_obj
def predict_image(obj, image):
    '''Get predictions for an image using a trained neural network or
    pipeline.'''

    dataset = obj['dataset']

    if 'pipeline' in obj:
        pipeline = dataset.get_pipeline(obj['pipeline'])
        r = pipeline.predict(image)
        print(json.dumps(r.to_dict()))
    else:
        network = dataset.get_network(obj['network'])
        if not network.is_trained():
            raise SystemExit("Please train neural network '{}' first".format(
                network.name))
        print(network.predict(image))


class Stats():

    def __init__(self, record=None, other_variables=()):
        self.record = record
        self.other = other_variables
        if record is not None:
            print('prediction', 'truth', *other_variables,
                  sep=',', file=record)
        self.observations = 0  # total observations
        self.hits = 0          # correct predictions (overall accuracy)
        self.detections = 0    # correct predictions
        self.true_clas = 0     # correct classifications

    def register(self, prediction, truth, **other_variables):
        self.observations += 1
        if truth == prediction:
            self.hits += 1
        if prediction is not None and truth is not None:
            self.detections += 1
            if truth == prediction:
                self.true_clas += 1
        if self.record is not None:
            print(prediction, truth,
                  *[other_variables[k] for k in self.other],
                  sep=',', file=self.record)

    def get_results(self):
        '''Get a dictionary of computed accuracies.'''
        return {
            'overall': safe_divide(self.hits, self.observations),
            'det_acc': safe_divide(self.detections, self.observations),
            'cls_acc': safe_divide(self.true_clas, self.detections),
        }


def safe_divide(a, b):
    return a / b if a != 0 and b != 0 else 0


@click.command('test')
@click.pass_obj
@click.option('--print/--no-print', '-p', 'do_print', default=True,
              help='Show results in the command line')
@click.option('--results-json/--no-results-json', default=False,
              help='Print results into a `results.json` file in the network directory')
@click.option('--predictions-csv/--no-predictions-csv', default=False,
              help='Print all predictions into a `predictions.csv` file in the network directory')
@click.option('--on-train', is_flag=True, default=False,
              help='Test the network on the train set instead of the test one')
def test(obj, do_print, results_json, predictions_csv, on_train):
    '''Compute evaluation metrics for a trained neural network or pipeline.

    By default annotations in test folds (see train/test split) are used.
    Accuracy is computed, and also separate accuracies for detection and
    classification. The full predictions can be printed into a csv for further
    analysis with statistics software.'''

    dataset = obj['dataset']

    if 'network' in obj:
        model = dataset.get_network(obj['network'])
        path = model.path
    elif 'pipeline' in obj:
        model = dataset.get_pipeline(obj['pipeline'])
        path = dataset.path / 'pipelines' / model.name

        def join_tags(tags, all_tags=dataset.config['g_tags']):
            return ''.join(tags.get(k, '') for k in all_tags)
    else:
        raise SystemExit("Please specify a network or a pipeline")

    prefix = 'train_' if on_train else ''

    record = None
    record_path = None
    if predictions_csv:
        record_path = path / f'{prefix}predictions.csv'
        path.mkdir(parents=True, exist_ok=True)
        record = open(record_path, 'w')

    if model.target == Target.GRAPH:
        stats = Stats(record, other_variables=('image', 'confidence'))
        test_fn = test_grapheme
    else:
        stats = Stats(record, other_variables=('image', 'confidence', 'iou'))
        test_fn = test_logogram

    if do_print:
        print("Annotations tested: 0", end='\r')
    n = 0

    if 'network' in obj:
        for an in model.get_annotations(not on_train):
            model.test(an, stats)
            if do_print:
                print("Annotations tested: {}".format(n), end='\r')
                n += 1
    elif 'pipeline' in obj:
        try:
            subsets = model.config.get('subsets')
        except AttributeError:
            subsets = None
        for an in dataset.get_annotations(model.target, subsets):
            if dataset.is_test(an):
                test_fn(model, an, stats, join_tags)
                if do_print:
                    print("Annotations tested: {}".format(n), end='\r')
                    n += 1

    if do_print:
        print("Annotations tested: {}".format(n))

    results = stats.get_results()

    if predictions_csv:
        record.close()

    if do_print:
        click.echo(json.dumps(results, indent=4))

    if results_json:
        path.mkdir(parents=True, exist_ok=True)
        file_path = path / f'{prefix}results.json'
        file_path.write_text(json.dumps(results))
        click.echo("Printed results to '{}'".format(file_path.resolve()))

    if predictions_csv:
        click.echo("Printed predictions to '{}'".format(record_path.resolve()))


def test_grapheme(pipeline, an, stats, join_tags):
    p = Grapheme(image=an.image)
    pipeline.run(p)
    truth = join_tags(an.tags)
    pred = join_tags(p.tags)
    stats.register(prediction=pred, truth=truth,
            image=an.image_path.relative_to(pipeline.dataset.path),
            confidence=p.meta.get('confidence', 0))


def test_logogram(pipeline, an, stats, join_tags):
    p = Logogram(image=an.image)
    pipeline.run(p)
    for x, y, iou in match(an.graphemes, p.graphemes):
        truth = join_tags(x.tags) if x is not None else None
        pred = join_tags(y.tags) if y is not None else None
        confidence = y.meta['confidence'] if y is not None else 0
        stats.register(prediction=pred, truth=truth,
                image=an.image_path.relative_to(pipeline.dataset.path),
                confidence=confidence, iou=iou)
