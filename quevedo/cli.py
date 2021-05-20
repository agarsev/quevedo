# 2020-04-08 Antonio F. G. Sevilla <afgs@ucm.es>
# Licensed under the Open Software License version 3.0

import click
from os import getcwd

from quevedo import darknet, web, dataset as ds
import quevedo.network.cli as network
from quevedo.extract_graphemes import extract_graphemes
from quevedo.generate import generate
from quevedo.run_script import run_script


@click.group(commands=[
    ds.train_test_split, ds.config_edit,
    ds.info, ds.create, ds.add_images,
    extract_graphemes, generate,
    network.prepare, network.train,
    network.predict_image, network.test,
    web.launcher, run_script,
], chain=True, invoke_without_command=True)
@click.option('-D', '--dataset', type=click.Path(), default=getcwd(),
              help="Path to the dataset to use, by default use current directory")
@click.option('-N', '--network', help="Neural network configuration to use")
@click.pass_context
def cli(ctx, dataset, network):
    '''Quevedo is a tool for managing datasets of images with compositional
    semantics.

    This includes file management, annotation of data, and neural network
    training and use.

    The -D and -N flags are global, and affect all commands used afterwards. For
    example, to run a full experiment for neural network 'one', run:

        quevedo -D path/to/dataset -N one split -p 80 prepare train test
    '''
    dataset = ds.Dataset(dataset)
    ctx.obj = {
        'dataset': dataset,
        'network': network
    }
    if ctx.invoked_subcommand is None:
        ctx.invoke(ds.info)
        click.echo(cli.get_help(ctx))


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
