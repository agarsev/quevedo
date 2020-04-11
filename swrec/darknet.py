# 2020-04-10 Antonio F. G. Sevilla <afgs@ucm.es>

import click
import json
from pathlib import Path
from string import Template
from subprocess import run

@click.command()
@click.pass_obj
def configure (dataset):
    ''' Creates the files needed for training darknet yolo on this dataset.

    The transcriptions in the `real` directory must have been tagged. Any
    transcriptions in the `generated` directory will also be used.'''

    real_d = dataset.path / 'real'
    dn_dir = dataset.path / 'darknet'
    dn_dir.mkdir(exist_ok = True)

    # Collect all symbol names/classes used while making darknet/yolo bounding
    # box files
    symbol_set = set()
    annotation_files = list(real_d.glob('*.json'))

    for an in annotation_files:
        annotation = json.loads(an.read_text())
        bboxes = []
        for s in annotation['symbols']:
            bboxes += "{} {} {} {} {}".format(s['name'], *s['box'])
            symbol_set.add(s['name'])
        an.with_suffix(".txt").write_text("\n".join(bboxes))

    num_classes = len(symbol_set)

    names_file = dn_dir / 'obj.names'
    names_file.write_text("\n".join(symbol_set))

    # Write train file with the list of files to train on, that is real +
    # generated transcriptions
    generated = list((dataset.path / 'generated').glob('*.png'))
    train_file = dn_dir / 'train.txt'
    train_file.write_text("\n".join(str(f.with_suffix(".png").resolve()) for f in
        annotation_files + generated))

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
    num_max_batches = num_classes * 500 # Recommended *2000, let's see
    template = Template((Path(__file__).parent / 'darknet.cfg').read_text())
    net_config = template.substitute(
            num_classes=num_classes,
            num_filters=((num_classes+5)*3),
            num_max_batches=num_max_batches,
            num_steps_1=int(num_max_batches*80/100),
            num_steps_2=int(num_max_batches*90/100))
    (dn_dir / 'darknet.cfg').write_text(net_config)

    click.echo("Darknet configuration ready")

@click.command()
@click.option('--darknetpath','-d',type=click.Path(exists=True),
        required=True, default="darknet/darknet",
        help="Path to the darknet executable")
@click.pass_obj
def train (dataset, darknetpath):
    ''' Trains a neural network to recognize the SW in this dataset.

    Uses the transcriptions and configuration created, and calls the darknet
    binary with the appropriate information.'''

    dn_dir = dataset.path / 'darknet'
    if not dn_dir.exists():
        raise SystemExit("Darknet not configured for this dataset, configure it first")

    darknet_data = (dn_dir / 'darknet.data').resolve()
    darknet_cfg = (dn_dir / 'darknet.cfg').resolve()
    run([darknetpath, 'detector', 'train', darknet_data, darknet_cfg])

@click.command()
@click.option('--darknetpath','-d',type=click.Path(exists=True),
        required=True, default="darknet/darknet",
        help="Path to the darknet executable")
@click.option('--image','-i',type=click.Path(exists=True),
        required=True, help="Image to predict")
@click.pass_obj
def test (dataset, darknetpath, image):
    ''' Test the neural network on an image.'''

    dn_dir = dataset.path / 'darknet'
    if not dn_dir.exists():
        raise SystemExit("Darknet not configured for this dataset, configure it first")

    darknet_data = (dn_dir / 'darknet.data').resolve()
    darknet_cfg = (dn_dir / 'darknet.cfg').resolve()
    weights = (dataset.path / 'weights' / 'darknet_final.weights').resolve()
    
    if not weights.exists():
        raise SystemExit("Neural network has not been trained")

    run([darknetpath, 'detector', 'test', darknet_data, darknet_cfg,
        weights, image])

