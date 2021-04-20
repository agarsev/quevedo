# 2020-05-04 Antonio F. G. Sevilla <afgs@ucm.es>

import click
from os import replace
from shutil import rmtree


@click.command()
@click.pass_obj
def prepare(obj):
    ''' Creates the files needed for training and testing darknet.

    Important: after moving (changing the path) of the dataset, this command
    *must* be called again before any additional training or predicting.'''

    dataset = obj['dataset']
    network = dataset.get_network(obj['network'])
    network.prepare()

    click.echo("Dataset ready for training")


@click.command()
@click.pass_obj
def train(obj):
    ''' Trains a neural network to recognize the SW in this dataset.

    Uses the annotations and configuration created, and calls the darknet
    binary with the appropriate information.'''

    dataset = obj['dataset']
    network = dataset.get_network(obj['network'])

    if not (network.path / 'darknet.cfg').exists():
        raise SystemExit("Please run pre-train command first")

    weight_d = network.path / 'weights'
    weight_d.mkdir(exist_ok=True)

    darknet_data = (network.path / 'darknet.data').resolve()
    darknet_cfg = (network.path / 'darknet.cfg').resolve()
    dataset.run_darknet(network.get_network_type(),
                        'train', darknet_data, darknet_cfg)

    replace(str(weight_d / 'darknet_final.weights'),
            str(network.path / 'darknet_final.weights'))
    rmtree(str(weight_d))
