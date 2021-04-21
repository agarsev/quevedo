# 2021-04-21 Antonio F. G. Sevilla <afgs@ucm.es>

import click

from .detect import DetectNet
from .classify import ClassifyNet


def create_network(dataset, name):
    config = dataset.config['network'][name]
    if config['task'] == 'detect':
        return DetectNet(dataset, name)
    elif config['task'] == 'classify':
        return ClassifyNet(dataset, name)
    raise ValueError('Unknown task {} for network {}'.format(
        config['task'], name))


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

    if not network.is_prepared():
        raise SystemExit("Please run prepare command first")

    network.train()
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
        raise SystemExit("Please train the neural network first")

    predictions = network.predict(image)
    print(predictions)
