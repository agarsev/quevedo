# 2020-04-08 Antonio F. G. Sevilla <afgs@ucm.es>

import click
from os import getcwd

from quevedo import darknet, web, dataset as ds
from quevedo.extract_graphemes import extract_graphemes
from quevedo.generate import generate
from quevedo.network import prepare, train


@click.group(commands={
    'split': ds.train_test_split, 'config': ds.config_edit,
    'extract': extract_graphemes, 'generate': generate,
    'prepare': prepare, 'train': train,
    'test': darknet.test, 'predict': darknet.predict_image,
    'info': ds.info, 'create': ds.create, 'add_images': ds.add_images,
    'web': web.launcher
}, chain=True, invoke_without_command=True)
@click.option('-D', '--dataset', type=click.Path(), default=getcwd(),
              help="Path to the dataset to use, by default use current directory")
@click.option('-N', '--network', help="Neural network configuration to use")
@click.pass_context
def cli(ctx, dataset, network):
    '''Command line application for managing a dataset of instances from a
    complex writing system, for example SignWriting, including annotation and
    deep learning.'''
    dataset = ds.Dataset(dataset)
    ctx.obj = {
        'dataset': dataset,
        'network': network
    }
    if ctx.invoked_subcommand is None:
        ctx.invoke(ds.info)
        click.echo(cli.get_help(ctx))
