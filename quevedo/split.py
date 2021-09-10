# 2020-09-10 Antonio F. G. Sevilla <afgs@ucm.es>
# Licensed under the Open Software License version 3.0

import click
import random

from quevedo.annotation import Target


@click.command('split')
@click.option('--grapheme-set', '-g', multiple=True, help="Grapheme set(s) to split.")
@click.option('--logogram-set', '-l', multiple=True, help="Logogram set(s) to split.")
@click.option('--seed', type=click.INT, help='A seed for the random split algorithm.')
@click.option('--percentage', '-p', type=click.IntRange(0, 100),
              help="Do a two-way split (by default lists are named 'train' and 'test')"
                   " with such percentage of annotations assigned to the first list")
@click.option('--number', '-n', type=int, help="Number of (equally sized) splits to make")
@click.option('--append', '-a', 'existing', flag_value='a',
              help="Append new graphemes to the list if it already exists.")
@click.option('--replace', '-r', 'existing', flag_value='r',
              help="Replace the old list with these graphemes if it already exists.")
@click.argument('names', nargs=-1)
@click.pass_obj
def split(obj, grapheme_set, logogram_set, seed, percentage, number, existing, names):
    '''Split files into train and test groups.

    The annotations in the given subsets will be split into a number of groups,
    and each added to the named list, so that later these lists can be used to
    train and test on separate groups of annotations.

    If the special value "_ALL_" for either grapheme or logogram sets is given,
    the list will include all sets for the chosen target. If a homogeneous split
    along sets is required, call this command once for each set, using the
    same list name and the "append" (-a) flag.'''

    dataset = obj['dataset']
    dataset.lists_path.mkdir(exist_ok=True)

    random.seed(seed)

    if len(grapheme_set) > 0:
        if len(logogram_set) > 0:
            raise click.UsageError("Grapheme and logogram sets can't be split "
                                   "at the same time")
        if grapheme_set[0] == '_ALL_':
            grapheme_set = None
        an = list(dataset.get_annotations(Target.GRAPH, grapheme_set))
    elif len(logogram_set) > 0:
        if logogram_set[0] == '_ALL_':
            logogram_set = None
        an = list(dataset.get_annotations(Target.LOGO, logogram_set))
    else:
        raise click.UsageError("Either grapheme or logogram sets to split are required")

    random.shuffle(an)

    def open_list(name, e=existing):
        path = dataset.lists_path / name
        if path.exists():
            if e is None:
                e = click.prompt("Target list {} already exists.\n"
                    "What to do? (a)ppend/(r)eplace/(c)ancel".format(name),
                    default='c')[0]
            if e == 'r':
                return open(path, 'w', encoding="utf-8")
            elif e == 'a':
                return open(path, 'a', encoding="utf-8")
            else:
                raise click.Abort()
        else:
            return open(path, 'w', encoding="utf-8")

    def getpath(an):
        return str(an.json_path.with_suffix('')
                     .relative_to(dataset.path))+'\n'

    if percentage is not None:
        if len(names) == 0:
            names = ['train', 'test']
        elif len(names) != 2:
            raise click.UsageError("For a two-way split (only) two names should be given.")
        amount = round(len(an) * percentage / 100)
    elif number is not None:
        if len(names) == 0:
            names = ['fold'+str(i) for i in range(number)]
        elif len(names) != number:
            raise click.UsageError("Number of splits and number of names don't match.")
        amount = round(len(an)/number)
    elif len(names) == 0:
        raise click.UsageError("Need one of: names of splits, number of splits, percentage")
    else:
        amount = round(len(an)/len(names))

    start = 0
    msg = "Annotations split into"
    for n in names:
        l = open_list(n)
        end = start+amount
        if end > len(an):
            end = len(an)
        l.writelines(getpath(t) for t in an[start:end])
        msg += " {} ({} files)".format(n, end-start)
        start += amount
        l.close()

    click.echo(msg)
