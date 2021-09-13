# 2020-04-07 Antonio F. G. Sevilla <afgs@ucm.es>
# Licensed under the Open Software License version 3.0

import click

from quevedo.annotation import Target


@click.command('extract')
@click.option('-f', '--from', 'dir_from', default='default',
              help='''Logogram subset from which to extract graphemes.''')
@click.option('-t', '--to', 'dir_to', default='default',
              help='''Grapheme subset where to place extracted graphemes.''')
@click.option('-m', '--merge', 'existing', flag_value='m',
              help='''Merge new graphemes with existing ones, if any.''')
@click.option('-r', '--replace', 'existing', flag_value='r',
              help='''Replace old graphemes with new ones, if any.''')
@click.pass_obj
def extract_graphemes(obj, dir_from, dir_to, existing):
    '''Extract graphemes from annotated logograms.

    This command takes all the logograms in the given subset, extracts the
    graphemes annotated in each of them, and stores them as independent
    annotations (carrying over the relevant information) in the chosen grapheme
    subset.'''

    dataset = obj['dataset']
    graph_d = dataset.create_subset(Target.GRAPH, dir_to, existing)

    for logo in dataset.get_annotations(Target.LOGO, subset=dir_from):
        for g in logo.graphemes:
            dataset.new_single(Target.GRAPH, dir_to, pil_image=g.image,
                               fold=logo.fold, tags=g.tags)

    (graph_d / 'README.md').write_text(
        'Graphemes extracted automatically from "{}" logograms'.format(dir_from))
