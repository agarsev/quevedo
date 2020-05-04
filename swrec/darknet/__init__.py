# 2020-04-10 Antonio F. G. Sevilla <afgs@ucm.es>

import click
import re
import swrec.darknet.train

@click.command()
@click.option('--image','-i',type=click.Path(exists=True),
        required=True, help="Image to predict")
@click.pass_obj
def test (dataset, image):
    ''' Test the neural network on an image.'''
    from swrec.darknet.test import init_darknet, predict
    init_darknet(dataset)
    print(predict(image))
