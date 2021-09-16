# 2020-09-10 Antonio F. G. Sevilla <afgs@ucm.es>
# Licensed under the Open Software License version 3.0

import click
from itertools import chain
import random

from quevedo.annotation import Target


@click.command('split')
@click.option('--grapheme-set', '-g', multiple=True, help="Grapheme set(s) to split.")
@click.option('--logogram-set', '-l', multiple=True, help="Logogram set(s) to split.")
@click.option('--start-fold', '-s', type=click.INT, default=0,
              help='Minimum number to use for the folds.')
@click.option('--end-fold', '-e', type=click.INT,
              help='Maximum number to use for the folds.')
@click.option('--seed', type=click.INT, help='A seed for the random split algorithm.')
@click.pass_obj
def split(obj, grapheme_set, logogram_set, start_fold, end_fold, seed):
    '''Assign annotations randomly to different folds.

    By default, the annotations will be split into a number of folds configured
    in the dataset configuration file, starting from 0. To override this, use
    the `-s` and `-e` option to change the range of values for the folds.  This
    can be used to ensure some particular subset of annotations is always
    assigned to some fold, for example one that will always be used for train or
    test.

    Which folds are to be used for training and which for testing can be
    configured in the dataset configuration file.

    If neither `-g` nor `-l` are used, all annotations in the dataset will be
    split, and if the special value "_ALL_" for either grapheme or logogram sets
    is given, all sets for the chosen target will be split. In the cases before,
    annotations will be assigned randomly, so no proportions of
    graphemes/logograms/sets can be guaranteed for any fold. If the same fold
    proportions in each set are desired, run the command once for each of
    them.'''

    dataset = obj['dataset']
    if end_fold is None:
        end_fold = dataset.config['folds']
    else:
        end_fold = end_fold + 1  # Exclusive ranges

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
    number = end_fold - start_fold
    amount = (len(an) // number)+((len(an) % number) > 0)

    start = 0
    for n in range(number):
        end = start+amount
        if end > len(an):
            end = len(an)
        for t in an[start:end]:
            t.fold = start_fold + n
            t.save()
        remainder = end-start
        start += amount
    click.echo("Annotations split into {} folds, of {} files "
       "(last fold {} files)".format(number, amount, remainder))
