# 2020-04-07 Antonio F. G. Sevilla <afgs@ucm.es>

import click
from PIL import Image

from quevedo.annotation import Annotation, Target


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
    graph_d = dataset.grapheme_path / dir_to

    try:
        graph_d.mkdir(parents=True)
    except FileExistsError:
        if existing is None:
            existing = click.prompt('Grapheme directory already exists.\n' +
                'What to do? (m)erge/(r)eplace/(a)bort', default='a')[0]
        if existing == 'r':
            for f in graph_d.glob('*'):
                f.unlink()
        elif existing == 'm':
            pass
        else:
            raise click.Abort()

    number = max((int(f.stem) for f in graph_d.glob('*.png')), default=0) + 1
    for t in dataset.get_annotations(Target.LOGO, subset=dir_from):
        number = number + 1
        logogram = Image.open(t.image)
        width, height = logogram.size
        for g in t.anot['graphemes']:
            w = float(g['box'][2]) * width
            h = float(g['box'][3]) * height
            l = float(g['box'][0]) * width - (w / 2)
            u = float(g['box'][1]) * height - (h / 2)
            region = logogram.crop((l, u, l + w, u + h))
            graph = Annotation(graph_d / str(number), target=Target.GRAPH)
            graph.create_from(pil_image=region, set=t.anot['set'],
                               tags=g['tags'])

    (graph_d / 'README.md').write_text(
        'Graphemes extracted automatically from "{}" logograms'.format(dir_from))
