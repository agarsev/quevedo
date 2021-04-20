# 2020-04-10 Antonio F. G. Sevilla <afgs@ucm.es>

import click
from quevedo.darknet.test import test


@click.command()
@click.option('--image', '-i', type=click.Path(exists=True),
              required=True, help="Image to predict")
@click.pass_obj
def predict_image(obj, image):
    '''Get predicted graphemes for an image using the trained neural network.'''
    from quevedo.darknet.predict import init_darknet, predict
    dataset = obj['dataset']
    network = dataset.get_network(obj['network'])
    init_darknet(dataset, network)
    print(predict(image, network))
