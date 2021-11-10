# 2021-05-07 Antonio F. G. Sevilla <afgs@ucm.es>
# Licensed under the Open Software License version 3.0

import click


@click.command('prepare')
@click.pass_obj
def prepare(obj):
    '''Create the files needed for training and using this network.

    The training files, net configuration, and mapping from dataset tags to
    net classes are stored in a directory named after the chosen net (-N flag)
    under the `networks` path.'''

    dataset = obj['dataset']
    network = dataset.get_network(obj['network'])

    network.prepare()
    click.echo("Neural network '{}' ready for training".format(network.name))


@click.command('train')
@click.option('--resume/--no-resume', '-c', default=True,
              help="Start training with existing weights from a previous run")
@click.pass_obj
def train(obj, resume):
    '''Train the neural network.

    The training configuration and files must have been created by running the
    command `prepare`.  The weights obtained after training are stored in the
    network directory: `/<dataset>/networks/<network_name>/darknet_final.weights`.
    '''

    dataset = obj['dataset']
    network = dataset.get_network(obj['network'])

    if not network.is_prepared():
        raise SystemExit("Please run prepare command first")

    initial = None
    if resume and (network.path / 'darknet_final.weights').exists():
        initial = 'darknet_final.weights'
        click.echo("Resuming training")

    weights = network.train(initial=initial)

    if weights is None:
        click.echo("Training interrupted, no weights produced")
    else:
        if weights != 'darknet_final.weights':
            click.echo("Training interrupted, using partial weights ({})".format(weights))
        click.echo("Neural network '{}' trained".format(network.name))
