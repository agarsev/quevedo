# 2020-09-10 Antonio F. G. Sevilla <afgs@ucm.es>
# Licensed under the Open Software License version 3.0

import click
from itertools import chain
import random

from quevedo.annotation import Target


@click.command('split')
@click.option('--grapheme-set', '-g', multiple=True, help="Grapheme set(s) to split.")
@click.option('--logogram-set', '-l', multiple=True, help="Logogram set(s) to split.")
@click.option('--seed', type=click.INT, help='A seed for the random split algorithm.')
@click.pass_obj
def split(obj, grapheme_set, logogram_set, seed):
    '''Assign annotations randomly to different folds.

    Configure the number of folds in the dataset configuration file, as well as
    which folds are to be used for training and which for testing.

    If neither `-g` nor `-l` are used, all annotations in the dataset will be
    split, and if the special value "_ALL_" for either grapheme or logogram sets
    is given, all sets for the chosen target will be split. In the cases before,
    annotations will be assigned randomly, so no proportions of
    graphemes/logograms/sets can be guaranteed for any fold. If the same fold
    proportions in each set are desired, run the command once for each of
    them.'''

    dataset = obj['dataset']
    number = dataset.config['folds']

    random.seed(seed)

    if len(grapheme_set) == 0 and len(logogram_set) == 0:
        an = dataset.get_annotations()
    else:
        an = ()
        if len(grapheme_set) > 0:
            if grapheme_set[0] == '_ALL_':
                grapheme_set = None
            an = chain(an, dataset.get_annotations(Target.GRAPH, grapheme_set))
        if len(logogram_set) > 0:
            if logogram_set[0] == '_ALL_':
                logogram_set = None
            an = chain(an, dataset.get_annotations(Target.LOGO, logogram_set))

    an = list(an)
    random.shuffle(an)
    amount = (len(an) // number)+((len(an) % number) > 0)

    start = 0
    for n in range(number):
        end = start+amount
        if end > len(an):
            end = len(an)
        for t in an[start:end]:
            t.fold = n
            t.save()
        remainder = end-start
        start += amount
    click.echo("Annotations split into {} folds, of {} files "
       "(last fold {} files)".format(number, amount, remainder))
