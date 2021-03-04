# 2020-05-04 Antonio F. G. Sevilla <afgs@ucm.es>

import click
from os import replace
from shutil import rmtree


@click.command()
@click.pass_obj
def prepare(obj):
    ''' Creates the files needed for training and testing darknet on this
    dataset and experiment.

    Important: after moving (changing the path) of the dataset, this command
    *must* be called again before any additional training or predicting.

    The transcriptions in the `real` directory must have been tagged. If enabled
    for this experiment, transcriptions in the `generated` directory will also
    be used.'''

    dataset = obj['dataset']
    experiment = dataset.get_experiment(obj['experiment'])
    experiment.prepare()

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
    dataset.run_darknet(experiment.get_network_type(),
                        'train', darknet_data, darknet_cfg)

    replace(str(weight_d / 'darknet_final.weights'),
            str(experiment.path / 'darknet_final.weights'))
    rmtree(str(weight_d))
