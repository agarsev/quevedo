# 2020-05-06 Antonio F. G. Sevilla <afgs@ucm.es>

import click
import json


def box(xc, yc, w, h):
    return {
        'l': float(xc) - float(w) / 2,
        'r': float(xc) + float(w) / 2,
        'b': float(yc) - float(h) / 2,
        't': float(yc) + float(h) / 2,
        'w': float(w),
        'h': float(h)
    }


def safe_divide(a, b):
    if a == 0:
        return 0
    elif b == 0:
        return 1
    else:
        return a / b


def iou(a, b):
    '''Intersection over union for boxes in x, y, w, h format'''
    a = box(*a)
    b = box(*b)
    # Intersection
    il = max(a['l'], b['l'])
    ir = min(a['r'], b['r'])
    ix = ir - il if ir > il else 0
    ib = max(a['b'], b['b'])
    it = min(a['t'], b['t'])
    iy = it - ib if it > ib else 0
    i = ix * iy
    # Sum (union = sum - inters)
    s = a['w'] * a['h'] + b['w'] * b['h']
    return safe_divide(i, (s - i))


def similarity(a, b):
    '''Similarity of graphemes.'''
    return iou(a['box'], b['box']) if (a['name'] == b['name']) else 0


def incr(dic, name):
    dic[name] = dic.get(name, 0) + 1


@click.command()
@click.pass_obj
@click.option('--print/--no-print', '-p', 'do_print', default=True,
              help='Show results in the command line')
@click.option('--csv/--no-csv', default=True,
              help='Print results into a `results.csv` file in the experiment directory')
def test(obj, do_print, csv):
    '''Compute evaluation metrics for a trained neural network.

    Only annotations marked as "test" (see train/test split) are used.
    Precision, recall and f-score are computed for each class.'''

    from quevedo.darknet.predict import init_darknet, predict

    dataset = obj['dataset']
    experiment = dataset.get_experiment(obj['experiment'])
    init_darknet(dataset, experiment)

    all_graphemes = set()
    true_positives = dict()
    false_positives = dict()
    false_negatives = dict()

    task = experiment.config['task']

    for an in experiment.get_annotations('test'):
        predictions = predict(an.image, experiment)
        if task == 'detect':
            for g in an.anot['graphemes']:
                tag = experiment.get_tag(g['tags'])
                logo = {'box': g['box'], 'name': tag}
                if tag not in all_graphemes:
                    all_graphemes.add(tag)
                if len(predictions) > 0:
                    similarities = sorted(((similarity(p, logo), i) for (i, p) in
                                          enumerate(predictions)), reverse=True)
                    (sim, idx) = similarities[0]
                    if sim > 0.7:
                        predictions.pop(idx)
                        incr(true_positives, tag)
                        continue
                incr(false_negatives, tag)
            # Unassigned predictions are false positives
            for pred in predictions:
                incr(false_positives, pred['name'])

        else:  # classify
            best = predictions[0]
            true_tag = experiment.get_tag(an.anot['tags'])
            if true_tag not in all_graphemes:
                all_graphemes.add(true_tag)
            # TODO thresholds should be configuration, in detect too
            if best['confidence'] < 0.5:  # no prediction
                if true_tag != '':
                    incr(false_negatives, true_tag)
            else:
                if true_tag == best['tag']:
                    incr(true_positives, true_tag)
                else:
                    incr(false_positives, best['tag'])

    results = {}
    for name in sorted(all_graphemes):
        tp = true_positives.get(name, 0)
        fp = false_positives.get(name, 0)
        fn = false_negatives.get(name, 0)
        prec = safe_divide(tp, tp + fp)
        rec = safe_divide(tp, tp + fn)
        results[name] = {
            'prec': prec,
            'rec': rec,
            'f': safe_divide(2 * prec * rec, prec + rec),
        }

    if do_print:
        header = "class      precision  recall f-score"
        click.echo("{}\n{}".format(header, "-" * len(header)))
        for name in sorted(all_graphemes):
            r = results[name]
            click.echo("{:10s} {:9.2f} {:7.2f} {:7.2f}".format(name,
                    r['prec'], r['rec'], r['f']))

    if csv:
        file_path = experiment.path / 'results.csv'
        with open(file_path, 'w') as f:
            print("class;precision;recall;f-score", file=f)
            for name in sorted(all_graphemes):
                r = results[name]
                print("{};{};{};{}".format(name, r['prec'], r['rec'],
                       r['f']), file=f)
        click.echo("\nPrinted results to '{}'".format(file_path.resolve()))
