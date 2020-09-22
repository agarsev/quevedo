# 2020-04-07 Antonio F. G. Sevilla <afgs@ucm.es>

import click
import json
from PIL import Image


@click.command()
@click.pass_obj
def extract_symbols(dataset):
    ''' Extracts the symbols from the *real* transcriptions into their own files.

    - Real transcriptions must be in the `real` directory of the dataset, and they
    must be annotated.

    - Symbols will be placed in the `symbols` directory. The filenames will
    consist of the symbol name/class from the annotation, followed by the number
    of the real transcription from which they were extracted, and their index
    within. So:

    `symbol_name.trans_id.symbol_index.png`
    '''

    real_d = dataset.path / 'real'
    symbol_d = dataset.path / 'symbols'
    try:
        symbol_d.mkdir()
    except FileExistsError:
        click.confirm('Symbol directory already exists. Overwrite?', abort=True)
        for f in symbol_d.glob('*.png'):
            f.unlink()

    for an in real_d.glob('*.json'):
        annotation = json.loads(an.read_text())
        if annotation['set'] != 'train':
            continue
        number = an.stem
        transcription = Image.open(real_d / '{}.png'.format(number))
        width, height = transcription.size
        for idx, symb in enumerate(annotation['symbols'], start=1):
            name = symb['name']
            w = float(symb['box'][2]) * width
            h = float(symb['box'][3]) * height
            l = float(symb['box'][0]) * width - (w / 2)
            u = float(symb['box'][1]) * height - (h / 2)
            region = transcription.crop((l, u, l + w, u + h))
            region.save(symbol_d / '{}.{}.{}.png'.format(name, number, idx))
