# 2020-04-07 Antonio F. G. Sevilla <afgs@ucm.es>

import click

from quevedo.annotation import Target


@click.command()
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
    '''Extracts graphemes from annotated logograms into their own files'''

    dataset = obj['dataset']
    graph_d = dataset.create_subset(Target.GRAPH, dir_to, existing)

    for logo in dataset.get_annotations(Target.LOGO, subset=dir_from):
        for g in logo.graphemes:
            img = g.extract()
            dataset.new_single(Target.GRAPH, dir_to, pil_image=img,
                               set=logo.set, tags=g.tags)

    (graph_d / 'README.md').write_text(
        'Graphemes extracted automatically from "{}" logograms'.format(dir_from))
