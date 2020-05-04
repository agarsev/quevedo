# 2020-04-08 Antonio F. G. Sevilla <afgs@ucm.es>

import click
from swrec import extract_symbols, generate, darknet, dataset as ds

@click.group(commands={
        'extract_symbols': extract_symbols.extract_symbols,
        'generate': generate.generate,
        'pre_train': darknet.pre_train,
        'train': darknet.train, 'test': darknet.test,
        'info': ds.info, 'create': ds.create, 'add_images': ds.add_images,
    }, chain=True, invoke_without_command=True)
@click.argument('dataset', type=click.Path())
@click.pass_context
def cli (ctx, dataset):
    '''Command line application for managing a SW deep learning dataset.'''
    ctx.obj = ds.Dataset(dataset)
    if ctx.invoked_subcommand is None:
        ctx.invoke(ds.info)
        click.echo(cli.get_help(ctx))

@cli.command()
@click.pass_obj
@click.option('-h','--host', default='localhost')
@click.option('-p','--port', default='5000')
@click.option('-m','--mount-path', default='', help="Mount path for the tagger application")
@click.option('--browser/--no-browser',default=True, help="Launch browser at the tagger location")
def tagger(dataset, host, port, browser, mount_path):
    ''' Run a web application for annotating the transcriptions in the dataset.

    The files in the `real` directory will be listed. For each, bounding boxes
    of symbols can be added, along with their class/name, and meanings for the
    whole transcription. The information will be saved along the real
    transcription with a `json` extension.
    '''
    from swrec.tagger import tagger

    click.echo("Loading dataset...")
    tagger.load_dataset(dataset)
    url = "http://{}:{}".format(host, port)

    click.echo("Starting tagger at {}".format(url));
    if browser:
        click.launch(url);

    tagger.run(host, port, mount_path)
