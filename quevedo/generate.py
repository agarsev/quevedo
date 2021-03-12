# 2020-04-08 Antonio F. G. Sevilla <afgs@ucm.es>

import click
import json
from PIL import Image
from PIL.ImageOps import invert
import random
import re

from quevedo.annotation import Annotation

# Used only if force layout
try:
    import numpy as np
    import forcelayout as fl

    can_use_force = True
except ImportError:
    can_use_force = False

# Default configuration, override in the dataset's config.toml file, using the key
# 'generate'
config = {
    'count': 500,  # Number of files to generate
    'seed': None,  # Random seed for generation
    'use_force': True,  # Use a force layout algorithm to distribute symbols
    'width_range': [300, 500],  # A range of possible widths
    'height_range': [300, 500],  # A range of possible heights
}


def put_symbol(canvas, x, y, file_info, name, rotate=False):
    '''Put a symbol into a transcription, and write the resulting darknet
    bounding box annotation.'''

    canvas_w = canvas.width
    canvas_h = canvas.height

    sim = Image.open(file_info['filename']).convert("RGBA")
    w = sim.width
    h = sim.height
    if rotate:
        if random.random() > 0.5:
            sim = sim.transpose(Image.FLIP_LEFT_RIGHT)
        turns = random.randint(0, 4)
        sim = sim.rotate(turns * 90, resample=Image.BILINEAR, expand=True)
        if turns % 2 > 0:
            w, h = h, w

    if x + w > canvas_w:
        x -= x + w - canvas_w + 2
    if y + h > canvas_h:
        y -= y + h - canvas_h + 2

    # Convert white pixels to transparent
    sim.putalpha(invert(sim.convert("L")))

    canvas.alpha_composite(sim, (x, y))
    return {
        'tags': file_info['tags'],
        'box': [(x + w / 2) / canvas_w, (y + h / 2) / canvas_h,
                w / canvas_w, h / canvas_h]
    }


def create_transcription(path, symbols):
    '''Creates an image with randomly placed symbols'''
    canvas_w = random.randint(*config['width_range'])
    canvas_h = random.randint(*config['height_range'])

    class_names = []    # list of the names of the symbols to place
    files = []          # list of the actual files
    rotate = []         # list of whether to rotate each symbol
    positions = []      # list of the positions

    def add_symbol(name, params):
        class_names.append(name)
        files.append(random.choice(params['files']))
        rotate.append(params['rotate'])
        positions.append([random.randint(0, canvas_w), random.randint(0, canvas_h)])

    # Iterate over the list of symbols to find how many to place of each
    for name, params in symbols.items():
        if params['mode'] == 'one' and random.random() < params['freq']:
            add_symbol(name, params)
        elif params['mode'] == 'many':
            for _ in range(random.randint(0, params['max'])):
                if random.random() < params['prob']:
                    add_symbol(name, params)

    #  Use force layout to spread symbols
    if can_use_force and config['use_force'] and len(positions) > 1:
        layout = fl.draw_spring_layout(dataset=np.array(positions), algorithm=fl.SpringForce)
        positions = layout.spring_layout()

        xs = positions[:, 0]
        max_x, min_x = max(xs), min(xs)
        scale_x = (canvas_w * .8) / (max_x - min_x)
        positions[:, 0] = (xs - min_x) * scale_x + canvas_w * .1

        ys = positions[:, 1]
        max_y, min_y = max(ys), min(ys)
        scale_y = (canvas_h * .8) / (max_y - min_y)
        positions[:, 1] = (ys - min_y) * scale_y + canvas_h * .1

    # Create the actual transcription
    canvas = Image.new("RGBA", (canvas_w, canvas_h), "white")
    symbols = [put_symbol(canvas, int(x), int(y), file_info, name, rotate)
               for [x, y], name, file_info, rotate
               in zip(positions, class_names, files, rotate)]
    Annotation(path).create_from(pil_image=canvas, symbols=symbols)


@click.command()
@click.option('-f', '--from', 'dir_from', default='default',
              help='''Symbol subset to use''')
@click.option('-t', '--to', 'dir_to', default='default',
              help='''Transcription subset where to place generated transcriptions''')
@click.option('-m', '--merge', 'existing', flag_value='m',
              help='''Merge new transcriptions with existing ones, if any.''')
@click.option('-r', '--replace', 'existing', flag_value='r',
              help='''Replace old transcriptions with new ones, if any.''')
@click.pass_obj
def generate(obj, dir_from, dir_to, existing):
    '''Generates artificial "transcriptions" for training (data augmentation) by
    randomly combining symbols together. Some direction can be given to the
    generation process, see options in config file. Only symbols marked for
    training will be used.'''

    dataset = obj['dataset']
    gen_d = dataset.path / 'real' / dir_to

    try:
        gen_d.mkdir()
    except FileExistsError:
        if existing is None:
            existing = click.prompt('''Transcription directory already exists.
                What to do? (m)erge/(r)eplace/(a)bort''', default='a')[0]
        if existing == 'r':
            for f in gen_d.glob('*'):
                f.unlink()
        elif existing == 'm':
            pass
        else:
            click.Abort()

    config.update(dataset.config.get('generate', {}))
    random.seed(config['seed'])

    tag_index = dataset.config['tag_schema'].index(config['tag'])

    for param in config['params']:
        param['match'] = re.compile(param['match'])

    # Find the different symbols to use
    symbols = {}
    for symbol in dataset.get_symbols(subset=dir_from):
        if symbol.anot['set'] != 'train':
            continue
        tags = symbol.anot['tags']
        name = tags[tag_index]
        if name in symbols:
            symbols[name]['files'].append({
                'filename': symbol.image.resolve(),
                'tags': tags,
            })
        else:
            s = {}
            for param in config['params']:
                if param['match'].match(name):
                    s.update(param)
                    break
            else:
                raise SystemExit("Configuration not found for symbol {}".format(name))
            s['files'] = [{
                'filename': symbol.image.resolve(),
                'tags': tags,
            }]
            symbols[name] = s

    # Generate as many transcriptions as requested, numbering them incrementally
    for i in range(config['count']):
        create_transcription(gen_d / str(i + 1), symbols)
