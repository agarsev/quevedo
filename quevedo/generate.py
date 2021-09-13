# 2020-04-08 Antonio F. G. Sevilla <afgs@ucm.es>
# Licensed under the Open Software License version 3.0

import click
from PIL import Image
from PIL.ImageOps import invert
import random
import re

from quevedo.annotation import Target

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
    'use_force': True,  # Use a force layout algorithm to distribute graphemes
    'width_range': [300, 500],  # A range of possible widths
    'height_range': [300, 500],  # A range of possible heights
}


def put_grapheme(canvas, x, y, file_info, name, rotate=False):
    '''Put a grapheme into a logogram, and write the resulting darknet
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


def create_logogram(graphemes):
    '''Creates an image with randomly placed graphemes'''
    canvas_w = random.randint(*config['width_range'])
    canvas_h = random.randint(*config['height_range'])

    class_names = []    # list of the names of the graphemes to place
    files = []          # list of the actual files
    rotate = []         # list of whether to rotate each grapheme
    positions = []      # list of the positions

    def add_grapheme(name, params):
        class_names.append(name)
        files.append(random.choice(params['files']))
        rotate.append(params['rotate'])
        positions.append([random.randint(0, canvas_w), random.randint(0, canvas_h)])

    # Iterate over the list of graphemes to find how many to place of each
    for name, params in graphemes.items():
        if params['mode'] == 'one' and random.random() < params['freq']:
            add_grapheme(name, params)
        elif params['mode'] == 'many':
            for _ in range(random.randint(0, params['max'])):
                if random.random() < params['prob']:
                    add_grapheme(name, params)

    #  Use force layout to spread graphemes
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

    # Create the actual logogram
    canvas = Image.new("RGBA", (canvas_w, canvas_h), "white")
    graphemes = [put_grapheme(canvas, int(x), int(y), file_info, name, rotate)
               for [x, y], name, file_info, rotate
               in zip(positions, class_names, files, rotate)]
    return canvas, graphemes


@click.command()
@click.option('-f', '--from', 'dir_from', default='default',
              help='''Grapheme subset to use''')
@click.option('-t', '--to', 'dir_to', default='default',
              help='''Logogram subset where to place generated logograms.''')
@click.option('-m', '--merge', 'existing', flag_value='m',
              help='''Merge new logograms with existing ones, if any.''')
@click.option('-r', '--replace', 'existing', flag_value='r',
              help='''Replace old logograms with new ones, if any.''')
@click.pass_obj
def generate(obj, dir_from, dir_to, existing):
    '''Generate artificial logograms from existing graphemes.

    This command creates new logograms in the chosen subset by
    randomly combining graphemes together. The generation process can be
    somewhat controlled in the configuration file.

    Since the goal of this process is to perform data augmentation for
    training, only graphemes in "train" folds will be used. Generated logograms
    will have the first fold use for training set as their fold.'''

    dataset = obj['dataset']
    dataset.create_subset(Target.LOGO, dir_to, existing)

    config.update(dataset.config.get('generate', {}))
    random.seed(config['seed'])
    tag_name = config['tag']

    for param in config['params']:
        param['match'] = re.compile(param['match'])

    # Find the different graphemes to use
    graphemes = {}
    for g in dataset.get_annotations(Target.GRAPH, subset=dir_from):
        if not dataset.is_train(g):
            continue
        tags = g.tags
        tag_value = g.tags.get(tag_name)
        if tag_value in graphemes:
            graphemes[tag_value]['files'].append({
                'filename': g.image_path,
                'tags': tags,
            })
        else:
            s = {}
            for param in config['params']:
                if param['match'].match(tag_value):
                    s.update(param)
                    break
            else:
                raise SystemExit("Configuration not found for grapheme {}".format(tag_value))
            s['files'] = [{
                'filename': g.image_path,
                'tags': tags,
            }]
            graphemes[tag_value] = s

    # Generate as many logograms as requested
    fold = dataset.config['train_folds'][0]
    for _ in range(config['count']):
        img, gs = create_logogram(graphemes)
        dataset.new_single(Target.LOGO, dir_to, pil_image=img,
            graphemes=gs, fold=fold)
