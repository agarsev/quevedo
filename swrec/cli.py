# 2020-04-08 Antonio F. G. Sevilla <afgs@ucm.es>

import click
from pathlib import Path
from swrec import extract_symbols, generate, yolo

class Dataset:
    def __init__ (self, path):
        self.path = Path(path)

@click.group(commands={
        'extract_symbols': extract_symbols.extract_symbols,
        'generate': generate.generate,
        'make_yolo_files': yolo.make_yolo_files
    }, chain=True)
@click.argument('dataset', type=click.Path(exists=True))
@click.pass_context
def cli (ctx, dataset):
    '''Command line application for managing a SW deep learning dataset.'''
    ctx.obj = Dataset(dataset)

@cli.command()
@click.pass_obj
@click.option('-h','--host',default='localhost')
@click.option('-p','--port',default='5000')
def tagger(dataset, host, port):
    ''' Run a web application for annotating the transcriptions in the dataset.

    The files in the `real` directory will be listed. For each, bounding boxes
    of symbols can be added, along with their class/name, and meanings for the
    whole transcription. The information will be saved along the real
    transcription with a `json` extension.
    '''
    from swrec.tagger import tagger

    click.echo("Loading dataset...")
    tagger.load_dataset(dataset.path)
    click.echo("Starting tagger at http://{}:{}".format(host, port));
    click.launch("http://{}:{}".format(host, port));
    tagger.app.run(host=host, port=port)
