
# 2021-11-10 Antonio F. G. Sevilla <afgs@ucm.es>
# Licensed under the Open Software License version 3.0

import click
import json

from quevedo import Target


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
            'overall': self.hits / self.observations,
            'det_acc': self.detections / self.observations,
            'cls_acc': self.true_clas / self.detections,
        }


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
    '''Compute evaluation metrics for a trained neural network.

    By default annotations in test folds (see train/test split) are used.
    Accuracy is computed, and also separate accuracies for detection and
    classification. The full predictions can be printed into a csv for further
    analysis with statistics software.'''

    dataset = obj['dataset']
    network = dataset.get_network(obj['network'])

    prefix = 'train_' if on_train else ''

    record = None
    record_path = None
    if predictions_csv:
        record_path = network.path / f'{prefix}predictions.csv'
        record = open(record_path, 'w')

    if network.target == Target.GRAPH:
        stats = Stats(record, other_variables=('image', 'confidence'))
    else:
        stats = Stats(record, other_variables=('image', 'confidence', 'iou'))

    for an in network.get_annotations(not on_train):
        network.test(an, stats)
    results = stats.get_results()

    if predictions_csv:
        record.close()

    if do_print:
        click.echo(json.dumps(results, indent=4))

    if results_json:
        file_path = network.path / f'{prefix}results.json'
        file_path.write_text(json.dumps(results))
        click.echo("Printed results to '{}'".format(file_path.resolve()))

    if predictions_csv:
        click.echo("Printed predictions to '{}'".format(record_path.resolve()))
