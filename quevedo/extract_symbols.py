# 2020-04-07 Antonio F. G. Sevilla <afgs@ucm.es>

import click
import json
from PIL import Image


@click.command()
@click.pass_obj
def extract_symbols(obj):
    '''Extracts the symbols from the *real* transcriptions into their own files,
    and places them in the `symbols` directory.'''

    dataset = obj['dataset']
    symbol_d = dataset.path / 'symbols'

    try:
        symbol_d.mkdir()
    except FileExistsError:
        click.confirm('Symbol directory already exists. Overwrite?', abort=True)
        for f in symbol_d.glob('*'):
            f.unlink()

    number = 0
    for t in dataset.get_real():
        if t.anot['set'] != 'train':
            continue
        number = number + 1
        transcription = Image.open(t.image)
        width, height = transcription.size
        for idx, symb in enumerate(t.anot['symbols'], start=1):
            w = float(symb['box'][2]) * width
            h = float(symb['box'][3]) * height
            l = float(symb['box'][0]) * width - (w / 2)
            u = float(symb['box'][1]) * height - (h / 2)
            region = transcription.crop((l, u, l + w, u + h))
            filename = symbol_d / ('{}_{}'.format(number, idx))
            region.save(filename.with_suffix('.png'))
            filename.with_suffix('.json').write_text(json.dumps({'tags': symb['tags']}))
