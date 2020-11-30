# 2020-05-04 Antonio F. G. Sevilla <afgs@ucm.es>

import click
from itertools import chain
from pathlib import Path
from string import Template
from shutil import move, rmtree


@click.command()
@click.pass_obj
def prepare(obj):
    ''' Creates the files needed for training and testing darknet yolo on this dataset and
    experiment.

    Important: after moving (changing the path) of the dataset, this command
    *must* be called again before any additional training or predicting.

    The transcriptions in the `real` directory must have been tagged. If enabled
    for this experiment, transcriptions in the `generated` directory will also
    be used.'''

    dataset = obj['dataset']
    experiment = dataset.get_experiment(obj['experiment'])
    experiment.path.mkdir(exist_ok=True)

    all_annotation_files = dataset.get_real()
    if experiment.info['generate']:
        all_annotation_files = chain(all_annotation_files, dataset.get_generated())

    annotation_files = [t for t in all_annotation_files if t.anot.get('set') == 'train']

    # Collect all symbol names/classes (1st pass)
    symbols = set()
    for t in annotation_files:
        symbols |= set(experiment.get_tag(s['tags'])
                       for s in t.anot['symbols'])
    # (we need two passes to get a sorted, and thus predictable, symbol list)
    symbols = sorted(symbols)
    num_classes = len(symbols)

    names_file = experiment.path / 'obj.names'
    names_file.write_text("\n".join(symbols) + "\n")

    # Write darknet/yolo bounding box files (2nd pass)
    for t in annotation_files:
        t._txt.write_text("".join("{} {} {} {} {}\n".format(
            symbols.index(experiment.get_tag(s['tags'])), *s['box'])
            for s in t.anot['symbols']))

    # Write train file with the list of files to train on, that is real +
    # generated transcriptions
    train_file = experiment.path / 'train.txt'
    train_file.write_text("\n".join(str(f.image.resolve())
                                    for f in annotation_files) + "\n")

    # In this directory, the weights of the trained network will be stored
    weight_d = experiment.path / 'weights'

    # Write meta-configuration information in the darknet data file
    (experiment.path / 'darknet.data').write_text(("classes = {}\n"
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
    (experiment.path / 'darknet.cfg').write_text(net_config)

    click.echo("Dataset ready for training")


@click.command()
@click.pass_obj
def train(obj):
    ''' Trains a neural network to recognize the SW in this dataset.

    Uses the transcriptions and configuration created, and calls the darknet
    binary with the appropriate information.'''

    dataset = obj['dataset']
    experiment = dataset.get_experiment(obj['experiment'])

    if not (experiment.path / 'darknet.cfg').exists():
        raise SystemExit("Please run pre-train command first")

    weight_d = experiment.path / 'weights'
    weight_d.mkdir(exist_ok=True)

    darknet_data = (experiment.path / 'darknet.data').resolve()
    darknet_cfg = (experiment.path / 'darknet.cfg').resolve()
    dataset.run_darknet('detector', 'train', darknet_data, darknet_cfg)

    move(str(weight_d / 'darknet_final.weights'), str(experiment.path))
    rmtree(str(weight_d))
