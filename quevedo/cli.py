# 2020-04-08 Antonio F. G. Sevilla <afgs@ucm.es>
# Licensed under the Open Software License version 3.0

import click
from os import getcwd

from quevedo import web, dataset as ds
import quevedo.network.cli as network
from quevedo.inference import predict_image, test
from quevedo.extract_graphemes import extract_graphemes
from quevedo.generate import generate
from quevedo.run_script import run_script
from quevedo.migrate import migrate
from quevedo.split import split


@click.group(commands=[
    ds.config_edit, ds.info, ds.create, ds.add_images,
    split, extract_graphemes, generate,
    network.prepare, network.train,
    predict_image, test,
    web.launcher, run_script, migrate,
], chain=True, invoke_without_command=True)
@click.option('-D', '--dataset', type=click.Path(), default=getcwd(),
              help="Path to the dataset to use, by default use current directory.")
@click.option('-N', '--network', help="Neural network configuration to use.")
@click.option('-P', '--pipeline', help="Pipeline configuration to use.")
@click.version_option()
@click.pass_context
def cli(ctx, dataset, network, pipeline):
    '''Quevedo is a tool for managing datasets of images with compositional
    semantics.

    This includes file management, annotation of data, and neural network
    training and use.

    The -D, -N and -P flags are global, and affect all commands used afterwards.
    -N and -P are exclusive. For example, to run a full experiment for neural
    network 'one', run:

        quevedo -D path/to/dataset -N one split -p 80 prepare train test
    '''

    if ctx.invoked_subcommand is None:
        click.echo(cli.get_help(ctx))
        return

    dataset = ds.Dataset(dataset)
    ctx.obj = {'dataset': dataset}

    if network is not None and pipeline is not None:
        raise click.UsageError("-N and -P are exclusive")

    if network is not None:
        ctx.obj['network'] = network
    elif pipeline is not None:
        ctx.obj['pipeline'] = pipeline


# Adapted from https://stackoverflow.com/a/58018765
def get_docs(cmd=cli, parent=None):
    name = cmd.name
    if name == 'cli':
        name = 'quevedo'
        print("# Command Line Interface\n\n```txt")
    else:
        print("\n## `{}`\n\n```txt".format(name))
    ctx = click.core.Context(cmd, info_name=name, parent=parent)
    print(cmd.get_help(ctx))
    print("```")
    commands = getattr(cmd, 'commands', {})
    for sub in commands.values():
        get_docs(sub, ctx)
