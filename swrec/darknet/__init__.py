# 2020-04-10 Antonio F. G. Sevilla <afgs@ucm.es>

import click
import swrec.darknet.train
from swrec.darknet.test import test


@click.command()
@click.option('--image', '-i', type=click.Path(exists=True),
              required=True, help="Image to predict")
@click.pass_obj
def predict_image(obj, image):
    '''Get predicted symbols for an image using the trained neural network.'''
    from swrec.darknet.predict import init_darknet, predict
    dataset = obj['dataset']
    experiment = dataset.get_experiment(obj['experiment'])
    init_darknet(dataset, experiment)
    print(predict(image))
