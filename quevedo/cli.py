# 2020-04-08 Antonio F. G. Sevilla <afgs@ucm.es>

import click
from os import getcwd
import time

from quevedo import darknet, web, dataset as ds
from quevedo.extract_symbols import extract_symbols
from quevedo.generate import generate


@click.group(commands={
    'split': ds.train_test_split, 'config': ds.config_edit,
    'extract_symbols': extract_symbols, 'generate': generate,
    'prepare': darknet.train.prepare, 'train': darknet.train.train,
    'test': darknet.test, 'predict': darknet.predict_image,
    'info': ds.info, 'create': ds.create, 'add_images': ds.add_images,
    'web': web.launcher
}, chain=True, invoke_without_command=True)
@click.option('-D', '--dataset', type=click.Path(), default=getcwd(),
              help="Path to the dataset to use, by default use current directory")
@click.option('-E', '--experiment', help="Experimental configuration to use")
@click.pass_context
def cli(ctx, dataset, experiment):
    '''Command line application for managing a SW deep learning dataset.'''
    dataset = ds.Dataset(dataset)
    ctx.obj = {
        'dataset': dataset,
        'experiment': experiment
    }
    if ctx.invoked_subcommand is None:
        ctx.invoke(ds.info)
        click.echo(cli.get_help(ctx))
