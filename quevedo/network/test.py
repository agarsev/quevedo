# 2020-05-06 Antonio F. G. Sevilla <afgs@ucm.es>
# Licensed under the Open Software License version 3.0

import click
from collections import Counter
import json


def safe_divide(a, b):
    return a / b if b else 0


class Stats():

    def __init__(self, record=None):
        self.record = record
        if record is not None:
            print('Prediction,Truth',
                  file=record)
        self.observations = Counter()
        self.true_positives = Counter()
        self.false_positives = Counter()
        self.false_negatives = Counter()

    def register(self, prediction, ground_truth):
        self.observations[ground_truth] += 1
        if prediction is None:
            self.false_negatives[ground_truth] += 1
        elif prediction == ground_truth:
            self.true_positives[prediction] += 1
        else:
            self.false_positives[prediction] += 1
        if self.record is not None:
            print('{},{}'.format(prediction, ground_truth),
                  file=self.record)

    def get_results(self):
        '''Get a dictionary of computed statistics.'''
        results = {}
        total_tp = 0
        total_fp = 0
        total_fn = 0
        total_obs = 0
        for name in sorted(tag for tag in self.observations.keys()
                           if tag is not None):
            total_obs += self.observations[name]
            tp = self.true_positives[name]
            total_tp += tp
            fp = self.false_positives[name]
            total_fp += fp
            fn = self.false_negatives[name]
            total_fn += fn
            prec = safe_divide(tp, tp + fp)
            rec = safe_divide(tp, tp + fn)
            results[name] = {
                'count': self.observations[name],
                'precision': prec,
                'recall': rec,
                'fscore': safe_divide(2 * prec * rec, prec + rec),
            }
        prec = safe_divide(total_tp, total_tp + total_fp)
        rec = safe_divide(total_tp, total_tp + total_fn)
        results['overall'] = {
            'count': total_obs,
            'precision': prec,
            'recall': rec,
            'fscore': safe_divide(2 * prec * rec, prec + rec),
        }
        return results


@click.command('test')
@click.pass_obj
@click.option('--print/--no-print', '-p', 'do_print', default=True,
              help='Show results in the command line')
@click.option('--results-csv/--no-results-csv', default=False,
              help='Print results into a `results.csv` file in the network directory')
@click.option('--results-json/--no-results-json', default=False,
              help='Print results into a `results.json` file in the network directory')
@click.option('--predictions-csv/--no-predictions-csv', default=False,
              help='Print all predictions into a `predictions.csv` file in the network directory')
@click.option('--on-train', is_flag=True, default=False,
              help='Test the network on the train set instead of the test one')
def test(obj, do_print, results_csv, results_json, predictions_csv, on_train):
    '''Compute evaluation metrics for a trained neural network.

    By default annotations marked as "test" (see train/test split) are used.
    Precision, recall and f-score are computed for each class, as well as global
    metrics (macro average). For more detailed statistics, the full predictions
    can be printed into a csv to be loaded into other software (like R).'''

    dataset = obj['dataset']
    network = dataset.get_network(obj['network'])

    record = None
    record_path = None
    if predictions_csv:
        record_path = network.path / 'predictions.csv'
        record = open(record_path, 'w')
    stats = Stats(record)

    test_set = 'train' if on_train else 'test'
    for an in network.get_annotations(test_set):
        network.test(an, stats)
    results = stats.get_results()

    if predictions_csv:
        record.close()

    if do_print:
        header = "class          count  precision  recall f-score"
        click.echo("{}\n{}".format(header, "-" * len(header)))
        for name, r in results.items():
            click.echo("{:15s} {count:4d} {precision:10.2f} "
                       "{recall:7.2f} {fscore:7.2f}".format(name, **r))
        click.echo("\n")

    if results_csv:
        file_path = network.path / 'results.csv'
        with open(file_path, 'w') as f:
            print("class,precision,recall,f-score", file=f)
            for name, r in results.items():
                print("{},{},{},{}".format(name, **r), file=f)
        click.echo("Printed results to '{}'".format(file_path.resolve()))

    if results_json:
        file_path = network.path / 'results.json'
        file_path.write_text(json.dumps(results))
        click.echo("Printed results to '{}'".format(file_path.resolve()))

    if predictions_csv:
        click.echo("Printed predictions to '{}'".format(record_path.resolve()))
