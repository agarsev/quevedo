# 2020-04-09 Antonio F. G. Sevilla <afgs@ucm.es>

import click
import json
from pathlib import Path
from shutil import copyfile
import yaml

class Dataset:
    ''' Class representing a SW dataset'''

    def __init__ (self, path):
        '''We lazy load the dataset path to allow the "create" command to create the
        directory but other commands to fail if it doesn't exist. This is due to how
        click works, and unlikely to be fixed. '''
        self._path = Path(path)

    def mkdir (self):
        if self._path.exists():
            raise SystemExit("Dataset '{}' already exists".format(self._path))
        self.path = self._path
        (self.path / 'real').mkdir(parents=True) # We also create the required real directory

    def __getattr__ (self, attr):
        if attr == 'path':
            if not self._path.exists():
                raise SystemExit("Dataset '{}' does not exist".format(self._path))
            self.path = self._path
            return self.path
        if attr == 'info':
            self.info = yaml.safe_load((self.path / 'info.yaml').read_text())
            return self.info

@click.command()
@click.pass_obj
def create(dataset):
    ''' Creates a dataset directory with the correct structure.'''
    dataset.mkdir()
    path = dataset.path

    title = click.prompt("Title of the dataset")
    description = click.prompt("Description of the dataset")

    default_info = (Path(__file__).parent / 'default_info.yaml').read_text()
    (path / 'info.yaml').write_text("title: {}\n\ndescription: {}\n\n{}".format(
        title, description, default_info))

    click.secho("Created dataset '{}' at '{}'\n".format(title, path), bold=True)


def style (condition, right, wrong=None):
    color = "green" if condition else "red"
    text = right if (condition or (wrong is None)) else wrong
    return click.style(str(text), fg=color)


@click.command()
@click.pass_obj
@click.option('--image_dir','-i', multiple=True, type=click.Path(exists=True),
        required=True, help="Directory from which to import images")
def add_images(dataset, image_dir):
    ''' Import images from directories to a dataset.'''

    real = dataset.path / 'real'
    idx = max((int(f.stem) for f in real.glob('*.png')), default=0) + 1
    for d in image_dir:
        click.echo("Importing images from '{}'... ".format(d), nl=False)
        count = 0
        d = Path(d)
        for img in d.glob('*.png'):
            new_name = real / str(idx)
            copyfile(img, new_name.with_suffix('.png'))
            new_name.with_suffix(".json").write_text(json.dumps({
                "meanings": [img.stem],
                "symbols": []
                }))
            idx = idx + 1
            count = count + 1
        click.echo("imported {}".format(style(count>0, count)))
    click.echo("\n")

def count (l):
    return sum(1 for _ in l)

@click.command()
@click.pass_obj
def info (dataset):
    ''' Returns status information about a dataset.'''

    path = dataset.path
    info = dataset.info
    click.secho('{}\n{}\n'.format(info["title"], '='*len(info['title'])), bold=True)
    click.echo(info["description"])

    real = path / 'real'
    num_real = count(real.glob('*.png'))
    click.echo('Real transcriptions: {}'.format(style(num_real>0, num_real)))
    num_annot = sum(len(json.loads(annot.read_text())['symbols'])>0
            for annot in real.glob('*.json'))
    click.echo('Annotated: {}/{}\n'.format(style(num_annot==num_real, num_annot),
        num_real))

    symbols = path / 'symbols'
    num_sym = count(symbols.glob('*.png'))
    click.echo('Symbols extracted: {}'.format(style(symbols.exists(), num_sym, 'no')))

    gen = path / 'generated'
    num_gen = count(gen.glob('*.png'))
    click.echo('Transcriptions generated: {}'.format(style(gen.exists(), num_gen, 'no')))

    darknet = path / 'darknet'
    num_txt = count(real.glob('*.txt')) + count(gen.glob('*.txt'))
    click.echo('Darknet {} configured and ready'.format(style(
        darknet.exists() and num_txt == num_gen+num_real,
        'is', "is not")))

    weights = path / 'weights' / 'darknet_final.weights'
    click.echo('Neural network {}'.format(style(weights.exists(),
        'has been trained', "hasn't been trained")))

    click.echo('')
