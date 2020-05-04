# 2020-04-10 Antonio F. G. Sevilla <afgs@ucm.es>

import click
import json
from pathlib import Path
from string import Template
import re

@click.command()
@click.pass_obj
def pre_train (dataset):
    ''' Creates the files needed for training darknet yolo on this dataset.

    The transcriptions in the `real` directory must have been tagged. Any
    transcriptions in the `generated` directory will also be used.'''

    real_d = dataset.path / 'real'
    dn_dir = dataset.path / 'darknet'
    dn_dir.mkdir(exist_ok = True)

    # Collect all symbol names/classes used while making darknet/yolo bounding
    # box files
    symbols = []
    annotation_files = (list(real_d.glob('*.json')) +
                        list((dataset.path / 'generated').glob('*.json')))

    for an in annotation_files:
        annotation = json.loads(an.read_text())
        bboxes = []
        for s in annotation['symbols']:
            try:
                index = symbols.index(s['name'])
            except ValueError:
                symbols.append(s['name'])
                index = len(symbols)-1
            bboxes.append("{} {} {} {} {}\n".format(index, *s['box']))
        an.with_suffix(".txt").write_text("".join(bboxes))

    num_classes = len(symbols)

    names_file = dn_dir / 'obj.names'
    names_file.write_text("\n".join(symbols)+"\n")

    # Write train file with the list of files to train on, that is real +
    # generated transcriptions
    train_file = dn_dir / 'train.txt'
    train_file.write_text("\n".join(str(f.with_suffix(".png").resolve())
        for f in annotation_files)+"\n")

    # In this directory, the weights of the trained network will be stored
    weight_d = dataset.path / 'weights'
    weight_d.mkdir(exist_ok = True)

    # Write meta-configuration information in the darknet data file
    (dn_dir / 'darknet.data').write_text(("classes = {}\n"
        "train = {}\nnames = {}\nbackup = {}\n").format(
            num_classes, train_file.resolve(),
            names_file.resolve(), weight_d.resolve()))

    # Write net configuration. See the darknet.cfg file provided from upstream,
    # the template is filled in here.
    num_max_batches = num_classes * 2000
    template = Template((Path(__file__).parent / 'darknet.cfg').read_text())
    net_config = template.substitute(
            num_classes=num_classes,
            num_filters=((num_classes+5)*3),
            num_max_batches=num_max_batches,
            num_steps_1=int(num_max_batches*80/100),
            num_steps_2=int(num_max_batches*90/100))
    (dn_dir / 'darknet.cfg').write_text(net_config)

    click.echo("Dataset ready for training")

@click.command()
@click.pass_obj
def train (dataset):
    ''' Trains a neural network to recognize the SW in this dataset.

    Uses the transcriptions and configuration created, and calls the darknet
    binary with the appropriate information.'''

    dn_dir = dataset.path / 'darknet'
    if not dn_dir.exists():
        raise SystemExit("Please run pre-train command first")

    darknet_data = (dn_dir / 'darknet.data').resolve()
    darknet_cfg = (dn_dir / 'darknet.cfg').resolve()
    dataset.run_darknet('detector', 'train', darknet_data, darknet_cfg)

@click.command()
@click.option('--image','-i',type=click.Path(exists=True),
        required=True, help="Image to predict")
@click.pass_obj
def test (dataset, image):
    ''' Test the neural network on an image.'''

    dn_dir = dataset.path / 'darknet'
    if not dn_dir.exists():
        raise SystemExit("Neural network has not been trained")

    darknet_data = (dn_dir / 'darknet.data').resolve()
    darknet_cfg = (dn_dir / 'darknet.cfg').resolve()
    weights = (dataset.path / 'weights' / 'darknet_final.weights').resolve()
    
    if not weights.exists():
        raise SystemExit("Neural network has not been trained")

    from swrec.pythondarknet import init, detect
    from ctypes import c_char_p
    from math import ceil, floor

    load_net, load_meta = init(dataset.info['darknet']['library'])

    def cstr (s):
        return c_char_p(s.encode('utf8'))

    net = load_net(cstr(str(darknet_cfg)), cstr(str(weights)), 0)
    meta = load_meta(cstr(str(darknet_data)))
    r = detect(net, meta, cstr(image))

    def make_bbox(x, y, w, h):
        return [floor(x-w/2), floor(y-h/2), ceil(w), ceil(h)]

    print([{
        'name': s.decode('utf8'),
        'confidence': c,
        'bbox': make_bbox(*b)
        } for (s, c, b) in r])

    # When running mAP, use flag -letter_box
    #dataset.run_darknet('detector', 'test', darknet_data, darknet_cfg, weights, image)
