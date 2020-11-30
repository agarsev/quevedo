# 2020-04-08 Antonio F. G. Sevilla <afgs@ucm.es>

import click
from os import getcwd
import time

from quevedo import darknet, web, dataset as ds
from quevedo.extract_symbols import extract_symbols
from quevedo.generate import generate


@click.group(commands={
    'split': ds.train_test_split,
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


@cli.command()
@click.option('--quiet', '-q', 'quiet', flag_value=True, default=False)
@click.option('--verbose', '-V', 'quiet', flag_value=False)
@click.pass_context
def run(ctx, quiet):
    '''Runs all commands for an experiment, from dataset preparation to training
    and up to testing the result. Configure options in `info.yaml`.'''

    dataset = ctx.obj['dataset']
    experiment = dataset.get_experiment(ctx.obj['experiment'])

    click.echo("[{}] Preparing dataset {}".format(time.asctime(), dataset.title))
    ctx.invoke(ds.train_test_split, **experiment.info.get('split', {}))
    if experiment.info.get('generate', False):
        try:
            ctx.invoke(extract_symbols)
        except click.Abort:
            pass
        try:
            ctx.invoke(generate)
        except click.Abort:
            pass

    ctx.invoke(darknet.train.prepare)
    click.echo("\n[{}] Starting to train neural network".format(time.asctime()))
    if quiet:
        from quevedo.darknet.predict import DarknetShutup
        with DarknetShutup():
            ctx.invoke(darknet.train.train)
    else:
        ctx.invoke(darknet.train.train)

    click.echo("\n[{}] Finished training. Testing results".format(time.asctime()))
    if quiet:
        test_options = {'do_print': False, 'csv': True}
    else:
        test_options = {'do_print': True, 'csv': True}
    ctx.invoke(darknet.test, **test_options)

    click.echo("\n[{}] Finished experiment".format(time.asctime()))
