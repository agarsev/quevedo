# 2021-05-07 Antonio F. G. Sevilla <afgs@ucm.es>
# Licensed under the Open Software License version 3.0

import click
from pathlib import Path

from .test import test


@click.command()
@click.pass_obj
def prepare(obj):
    ''' Creates the files needed for training and testing darknet.

    Important: after moving (changing the path) of the dataset, this command
    *must* be called again before any additional training or predicting.'''

    dataset = obj['dataset']
    network = dataset.get_network(obj['network'])

    network.prepare()
    click.echo("Neural network '{}' ready for training".format(network.name))


@click.command()
@click.option('--resume/--no-resume', '-c', default=True,
              help="Start training with existing weights from a previous run")
@click.pass_obj
def train(obj, resume):
    ''' Trains a neural network to recognize the SW in this dataset.

    Uses the annotations and configuration created, and calls the darknet
    binary with the appropriate information.'''

    dataset = obj['dataset']
    network = dataset.get_network(obj['network'])

    if not network.is_prepared():
        raise SystemExit("Please run prepare command first")

    initial = None
    if resume and (network.path / 'darknet_final.weights').exists():
        initial = 'darknet_final.weights'
        click.echo("Resuming training")

    weights = network.train(initial=initial)

    if weights is None:
        click.echo("Training interrupted, no weights produced")
    else:
        if weights != 'darknet_final.weights':
            click.echo("Training interrupted, using partial weights ({})".format(weights))
        click.echo("Neural network '{}' trained".format(network.name))


@click.command()
@click.option('--image', '-i', type=click.Path(exists=True),
              required=True, help="Image to predict")
@click.pass_obj
def predict_image(obj, image):
    '''Get predictions for an image using the trained neural network.'''

    dataset = obj['dataset']
    network = dataset.get_network(obj['network'])

    if not network.is_trained():
        raise SystemExit("Please train neural network '{}' first".format(
            network.name))

    predictions = network.predict(image)
    print(predictions)
