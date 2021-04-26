# 2020-05-06 Antonio F. G. Sevilla <afgs@ucm.es>

import click
from collections import Counter


def safe_divide(a, b):
    return a / b if b else 0


class Stats():

    def __init__(self):
        self.all_tags = set()
        self.true_positives = Counter()
        self.false_positives = Counter()
        self.false_negatives = Counter()

    def add(self, tag):
        '''Add an observed class (tag).'''
        if tag not in self.all_tags:
            self.all_tags.add(tag)

    def get_results(self):
        '''Get a dictionary of computed statistics.'''
        results = {}
        total_tp = 0
        total_fp = 0
        total_fn = 0
        for name in sorted(self.all_tags):
            tp = self.true_positives[name]
            total_tp += tp
            fp = self.false_positives[name]
            total_fp += fp
            fn = self.false_negatives[name]
            total_fn += fn
            prec = safe_divide(tp, tp + fp)
            rec = safe_divide(tp, tp + fn)
            results[name] = {
                'prec': prec,
                'rec': rec,
                'f': safe_divide(2 * prec * rec, prec + rec),
            }
        prec = safe_divide(total_tp, total_tp + total_fp)
        rec = safe_divide(total_tp, total_tp + total_fn)
        results['overall'] = {
            'prec': prec,
            'rec': rec,
            'f': safe_divide(2 * prec * rec, prec + rec),
        }
        return results


@click.command()
@click.pass_obj
@click.option('--print/--no-print', '-p', 'do_print', default=True,
              help='Show results in the command line')
@click.option('--csv/--no-csv', default=True,
              help='Print results into a `results.csv` file in the network directory')
def test(obj, do_print, csv):
    '''Compute evaluation metrics for a trained neural network.

    Only annotations marked as "test" (see train/test split) are used.
    Precision, recall and f-score are computed for each class.'''

    dataset = obj['dataset']
    network = dataset.get_network(obj['network'])
    network.load()

    stats = Stats()
    for an in network.get_annotations('test'):
        network.test(an, stats)
    results = stats.get_results()

    if do_print:
        header = "class      precision  recall f-score"
        click.echo("{}\n{}".format(header, "-" * len(header)))
        for name, r in results.items():
            click.echo("{:10s} {:9.2f} {:7.2f} {:7.2f}".format(name,
                    r['prec'], r['rec'], r['f']))

    if csv:
        file_path = network.path / 'results.csv'
        with open(file_path, 'w') as f:
            print("class;precision;recall;f-score", file=f)
            for name, r in results.items():
                print("{};{};{};{}".format(name, r['prec'], r['rec'],
                       r['f']), file=f)
        click.echo("\nPrinted results to '{}'".format(file_path.resolve()))
