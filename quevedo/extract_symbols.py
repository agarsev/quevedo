# 2020-04-07 Antonio F. G. Sevilla <afgs@ucm.es>

import click
from PIL import Image

from quevedo.annotation import Annotation, Target


@click.command()
@click.option('-f', '--from', 'dir_from', default='default',
              help='''Transcription subset from which to extract symbols''')
@click.option('-t', '--to', 'dir_to', default='default',
              help='''Symbol subset where to place extracted symbols''')
@click.option('-m', '--merge', 'existing', flag_value='m',
              help='''Merge new symbols with existing ones, if any.''')
@click.option('-r', '--replace', 'existing', flag_value='r',
              help='''Replace old symbols with new ones, if any.''')
@click.pass_obj
def extract_symbols(obj, dir_from, dir_to, existing):
    '''Extracts symbols from annotated transcriptions into their own files'''

    dataset = obj['dataset']
    symbol_d = dataset.symbol_path / dir_to

    try:
        symbol_d.mkdir(parents=True)
    except FileExistsError:
        if existing is None:
            existing = click.prompt('Symbol directory already exists.\n' +
                'What to do? (m)erge/(r)eplace/(a)bort', default='a')[0]
        if existing == 'r':
            for f in symbol_d.glob('*'):
                f.unlink()
        elif existing == 'm':
            pass
        else:
            raise click.Abort()

    number = max((int(f.stem) for f in symbol_d.glob('*.png')), default=0) + 1
    for t in dataset.get_annotations(Target.TRAN, subset=dir_from):
        number = number + 1
        transcription = Image.open(t.image)
        width, height = transcription.size
        for symb in t.anot['symbols']:
            w = float(symb['box'][2]) * width
            h = float(symb['box'][3]) * height
            l = float(symb['box'][0]) * width - (w / 2)
            u = float(symb['box'][1]) * height - (h / 2)
            region = transcription.crop((l, u, l + w, u + h))
            symbol = Annotation(symbol_d / str(number), target=Target.SYMB)
            symbol.create_from(pil_image=region, set=t.anot['set'],
                               tags=symb['tags'])

    (symbol_d / 'README.md').write_text(
        'Symbols extracted automatically from {}'.format(dir_from))
