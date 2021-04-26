# 2020-04-08 Antonio F. G. Sevilla <afgs@ucm.es>

import click
from os import getcwd

from quevedo import darknet, web, network, dataset as ds
from quevedo.extract_graphemes import extract_graphemes
from quevedo.generate import generate
from quevedo.run_script import run_script


@click.group(commands={
    'split': ds.train_test_split, 'config': ds.config_edit,
    'extract': extract_graphemes, 'generate': generate,
    'prepare': network.prepare, 'train': network.train,
    'predict': network.predict_image, 'test': network.test,
    'info': ds.info, 'create': ds.create, 'add_images': ds.add_images,
    'web': web.launcher, 'run_script': run_script,
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
