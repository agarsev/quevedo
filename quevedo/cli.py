# 2020-04-08 Antonio F. G. Sevilla <afgs@ucm.es>

import click
from os import getcwd
from quevedo import extract_symbols, generate, darknet, migrate, dataset as ds


@click.group(commands={
    'split': ds.train_test_split,
    'extract_symbols': extract_symbols.extract_symbols,
    'generate': generate.generate,
    'pre_train': darknet.train.prepare, 'train': darknet.train.train,
    'test': darknet.test, 'predict': darknet.predict_image,
    'migrate': migrate.migrate,
    'info': ds.info, 'create': ds.create, 'add_images': ds.add_images,
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
@click.pass_obj
@click.option('-h', '--host', default='localhost')
@click.option('-p', '--port', default='5000')
@click.option('-m', '--mount-path', default='', help="Mount path for the web application")
@click.option('--browser/--no-browser', default=True, help="Launch browser with the web app")
def web(obj, host, port, browser, mount_path):
    ''' Run a web application for managing and annotating the transcriptions in
    the dataset.
    '''
    from quevedo.web import app

    dataset = obj['dataset']
    click.echo("Loading dataset '{}'...".format(dataset.info['title']))
    app.load_dataset(dataset)
    url = "http://{}:{}".format(host, port)

    click.echo("Starting app at {}".format(url))
    if browser:
        click.launch(url)

    app.run(host, port, mount_path)