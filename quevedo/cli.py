# 2020-04-08 Antonio F. G. Sevilla <afgs@ucm.es>

import click
from os import getcwd
from quevedo import extract_symbols, generate, darknet, migrate, web, dataset as ds


@click.group(commands={
    'split': ds.train_test_split,
    'extract_symbols': extract_symbols.extract_symbols,
    'generate': generate.generate,
    'pre_train': darknet.train.prepare, 'train': darknet.train.train,
    'test': darknet.test, 'predict': darknet.predict_image,
    'migrate': migrate.migrate,
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
