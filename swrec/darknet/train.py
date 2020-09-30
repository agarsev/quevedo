# 2020-05-04 Antonio F. G. Sevilla <afgs@ucm.es>

import click
from itertools import chain
import json
from pathlib import Path
from string import Template


@click.command()
@click.pass_obj
def prepare(dataset):
    ''' Creates the files needed for training darknet yolo on this dataset.

    The transcriptions in the `real` directory must have been tagged. Any
    transcriptions in the `generated` directory will also be used.'''

    real_d = dataset.path / 'real'
    dn_dir = dataset.path / 'darknet'
    dn_dir.mkdir(exist_ok=True)

    # Collect all symbol names/classes used while making darknet/yolo bounding
    # box files
    symbols = []
    annotation_files = []

    def get_tag(sym):
        return sym['tags'][0]

    for an in chain(real_d.glob('*.json'),
                    (dataset.path / 'generated').glob('*.json')):
        annotation = json.loads(an.read_text())
        if annotation.get('set', 'train') != 'train':
            continue
        bboxes = []
        for s in annotation['symbols']:
            tag = get_tag(s)
            try:
                index = symbols.index(tag)
            except ValueError:
                symbols.append(tag)
                index = len(symbols) - 1
            bboxes.append("{} {} {} {} {}\n".format(index, *s['box']))
        an.with_suffix(".txt").write_text("".join(bboxes))
        annotation_files.append(an)

    num_classes = len(symbols)

    names_file = dn_dir / 'obj.names'
    names_file.write_text("\n".join(symbols) + "\n")

    # Write train file with the list of files to train on, that is real +
    # generated transcriptions
    train_file = dn_dir / 'train.txt'
    train_file.write_text("\n".join(str(f.with_suffix(".png").resolve())
                                    for f in annotation_files) + "\n")

    # In this directory, the weights of the trained network will be stored
    weight_d = dataset.path / 'weights'
    weight_d.mkdir(exist_ok=True)

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
        num_filters=((num_classes + 5) * 3),
        num_max_batches=num_max_batches,
        num_steps_1=int(num_max_batches * 80 / 100),
        num_steps_2=int(num_max_batches * 90 / 100))
    (dn_dir / 'darknet.cfg').write_text(net_config)

    click.echo("Dataset ready for training")


@click.command()
@click.pass_obj
def train(dataset):
    ''' Trains a neural network to recognize the SW in this dataset.

    Uses the transcriptions and configuration created, and calls the darknet
    binary with the appropriate information.'''

    dn_dir = dataset.path / 'darknet'
    if not dn_dir.exists():
        raise SystemExit("Please run pre-train command first")

    darknet_data = (dn_dir / 'darknet.data').resolve()
    darknet_cfg = (dn_dir / 'darknet.cfg').resolve()
    dataset.run_darknet('detector', 'train', darknet_data, darknet_cfg)
