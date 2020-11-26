# 2020-04-09 Antonio F. G. Sevilla <afgs@ucm.es>

import click
from pathlib import Path
import random
from shutil import copyfile
from string import Template
from subprocess import run
import yaml

from quevedo.experiment import Experiment
from quevedo.transcription import Transcription


class Dataset:
    ''' Class representing a SW dataset'''

    def __init__(self, path):
        '''We lazy load the dataset path to allow the "create" command to create the
        directory but other commands to fail if it doesn't exist. This is due to how
        click works, and unlikely to be fixed. '''
        self._path = Path(path)

    def mkdir(self):
        if self._path.exists():
            raise SystemExit("Dataset '{}' already exists".format(self._path))
        self.path = self._path
        (self.path / 'real').mkdir(parents=True)  # We also create the required real directory
        (self.path / 'experiments').mkdir()

    def run_darknet(self, *args):
        darknet = self.info.get('darknet')
        if darknet is None:
            raise SystemExit("Darknet not configured for this dataset, configure it first")
        run([darknet['path'], *args, *darknet['options']])

    def list_experiments(self):
        return [e.stem for e in self.path.glob('experiments/*.yaml')]

    def get_experiment(self, name):
        if name is None:
            return Experiment(self, self.info['default_experiment'])
        else:
            return Experiment(self, name)

    def get_real(self):
        '''Returns a generator that yields all real annotations'''
        return (Transcription(file) for file in
                (self.path / 'real').glob('**/*.png'))

    def get_generated(self):
        '''Returns a generator that yields all generated annotations'''
        return (Transcription(file) for file in
                (self.path / 'generated').glob('*.png'))

    def __getattr__(self, attr):
        if attr == 'path':
            if not self._path.exists():
                raise SystemExit("Dataset '{}' does not exist".format(self._path))
            self.path = self._path
            return self.path
        if attr == 'info':
            info_path = self.path / 'info.yaml'
            if not info_path.exists():
                raise SystemExit("Path '{}' is not a valid dataset".format(self._path))
            self.info = yaml.safe_load(info_path.read_text())
            return self.info


@click.command()
@click.pass_obj
def create(obj):
    ''' Creates a dataset directory with the correct structure.'''
    dataset = obj['dataset']

    dataset.mkdir()
    path = dataset.path

    title = click.prompt("Title of the dataset")
    description = click.prompt("Description of the dataset")

    default_info = Template((Path(__file__).parent / 'default_info.yaml').read_text())
    (path / 'info.yaml').write_text(default_info.substitute(
        title=title, description=description))

    copyfile((Path(__file__).parent / 'default_experiment.yaml'),
             (path / 'experiments') / 'default.yaml')

    click.secho(("Created dataset '{}' at '{}'\n"
                "Please read and edit '{}'/info.yaml to adapt it for the dataset")
                .format(title, path, path), bold=True)


def style(condition, right, wrong=None):
    color = "green" if condition else "red"
    text = right if (condition or (wrong is None)) else wrong
    return click.style(str(text), fg=color)


@click.command()
@click.pass_obj
@click.option('--image_dir', '-i', multiple=True, type=click.Path(exists=True),
              required=True, help="Directory from which to import images")
@click.option('--name', '-n', help="Name for the subset of the dataset where to import the images")
def add_images(obj, image_dir, name='default'):
    ''' Import images from directories to a dataset.'''
    dataset = obj['dataset']

    dest = dataset.path / 'real' / name
    dest.mkdir(parents=True, exist_ok=True)

    idx = max((int(f.stem) for f in dest.glob('*.png')), default=0) + 1
    for d in image_dir:
        click.echo("Importing images from '{}' to '{}'...".format(
            d, dest.resolve()), nl=False)
        num = 0
        d = Path(d)
        for img in d.glob('*.png'):
            new_trans = Transcription(dest / str(idx))
            new_trans.create_from(img)
            idx = idx + 1
            num = num + 1
        click.echo("imported {}".format(style(num > 0, num)))
    click.echo("\n")


@click.command()
@click.argument('train_percentage', type=click.IntRange(0, 100))
@click.option('--seed', '-s', type=click.INT, help='A seed for the random split algorithm.')
@click.pass_obj
def train_test_split(obj, train_percentage, seed):
    '''Split real annotation files into two sets, one for training and one for
    test. Test files will not be used for symbol extraction either. The split is
    common to all experiments.'''
    dataset = obj['dataset']

    random.seed(seed)

    real = list(dataset.get_real())
    random.shuffle(real)

    split_point = round(len(real) * train_percentage / 100)

    for t in real[:split_point]:
        t.anot['set'] = 'train'
        t.save()

    for t in real[split_point:]:
        t.anot['set'] = 'test'
        t.save()

    click.echo("Dataset split into train ({} files) and test ({} files)".format(
               split_point, len(real) - split_point))


def count(l):
    return sum(1 for _ in l)


@click.command()
@click.pass_obj
def info(obj):
    ''' Returns status information about a dataset.'''
    dataset = obj['dataset']

    path = dataset.path
    info = dataset.info
    click.secho('{}\n{}'.format(info["title"], '▔' * len(info['title'])), bold=True)
    click.echo(info["description"])
    click.secho('Tag schema: {}\n'.format(', '.join(info["tag_schema"])), bold=True)

    real = list(dataset.get_real())
    num_real = count(real)
    click.echo('Real transcriptions: {}'.format(style(num_real > 0, num_real)))
    num_annot = sum(len(t.anot['symbols']) > 0 for t in real)
    click.echo('Annotated: {}/{}'.format(
        style(num_annot == num_real, num_annot), num_real))

    symbols = path / 'symbols'
    num_sym = count(symbols.glob('*.png'))
    click.echo('Symbols extracted: {}'.format(style(symbols.exists(), num_sym, 'no')))

    gen = path / 'generated'
    num_gen = count(gen.glob('*.png'))
    click.echo('Transcriptions generated: {}'.format(style(gen.exists(), num_gen, 'no')))

    dn_binary = (dataset.info.get('darknet', {}).get('path'))
    click.echo('Darknet {} properly configured in info.yaml'.format(
        style(dn_binary is not None and Path(dn_binary).exists(), 'is', 'is not')))

    exps = dataset.list_experiments()
    if len(exps) > 1:
        click.echo('\nExperiments:')
        for e in dataset.list_experiments():
            exp = dataset.get_experiment(e)
            click.echo('- {}: {}'.format(e, exp.info['subject']))

    experiment = dataset.get_experiment(obj['experiment'])

    header = "Experiment: '{}'".format(experiment.name)
    click.secho("\n{}\n{}".format(header, '▔' * len(header)), bold=True)
    click.echo("{}\n".format(experiment.info['subject']))

    darknet = experiment.path / 'darknet.cfg'
    num_txt = sum(1 for r in real if r._txt.exists()) + count(gen.glob('*.txt'))
    click.echo('Dataset {} ready for training'.format(style(
        darknet.exists() and num_txt == num_gen + num_real,
        'is', "is not")))

    weights = experiment.path / 'darknet_final.weights'
    click.echo('Neural network {}'.format(style(weights.exists(),
               'has been trained', "hasn't been trained")))

    click.echo('')
