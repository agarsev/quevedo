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
    '''Similarity of symbols.'''
    return iou(a['box'], b['box']) if (a['name'] == b['name']) else 0


def incr(dic, name):
    dic[name] = dic.get(name, 0) + 1


@click.command()
@click.pass_obj
def test(dataset):
    '''Compute evaluation metrics for the trained neural network.

    The transcriptions in the test set are used (so a train/test split must have
    been done) and precision, recall and f-score are computed for each class.'''

    from swrec.darknet.predict import init_darknet, predict
    init_darknet(dataset)

    all_symbols = set()
    true_positives = dict()
    false_positives = dict()
    false_negatives = dict()

    def get_tag(sym):
        return sym['tags'][0]

    for image in (dataset.path / 'real').glob('*.png'):
        anot = json.loads(image.with_suffix('.json').read_text())
        if anot.get('set') != 'test':
            continue
        predictions = predict(image)
        for sym in anot['symbols']:
            tag = get_tag(sym)
            real = {'box': sym['box'], 'name': tag}
            if tag not in all_symbols:
                all_symbols.add(tag)
            if len(predictions) > 0:
                similarities = sorted(((similarity(p, real), i) for (i, p) in
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

    header = "symbol     precision  recall f-score"
    click.echo("{}\n{}".format(header, "-" * len(header)))
    for name in sorted(all_symbols):
        tp = true_positives.get(name, 0)
        fp = false_positives.get(name, 0)
        fn = false_negatives.get(name, 0)
        prec = safe_divide(tp, tp + fp)
        rec = safe_divide(tp, tp + fn)
        f = safe_divide(2 * prec * rec, prec + rec)
        click.echo("{:10s} {:9.2f} {:7.2f} {:7.2f}".format(name, prec, rec, f))
