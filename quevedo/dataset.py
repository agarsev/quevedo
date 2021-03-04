# 2020-04-09 Antonio F. G. Sevilla <afgs@ucm.es>

import click
from os import listdir
from pathlib import Path
import random
from string import Template
from subprocess import run
import toml

from quevedo.experiment import Experiment
from quevedo.transcription import Transcription


class Dataset:
    ''' Class representing a SW dataset'''

    def __init__(self, path):
        '''We lazy load the dataset path to allow the "create" command to create the
        directory but other commands to fail if it doesn't exist. This is due to how
        click works, and unlikely to be fixed. '''
        self._path = Path(path)
        self.config_path = self._path / 'config.toml'

    def create(self):
        p = self._path
        if p.exists() and len(listdir(p))>0:
            raise SystemExit("Directory '{}' not empty, aborting".format(p.resolve()))
        self.path = p
        (self.path / 'real').mkdir(parents=True)  # We also create the required real directory
        (self.path / 'experiments').mkdir()

    def run_darknet(self, *args):
        darknet = self.config.get('darknet')
        if darknet is None:
            raise SystemExit("Darknet not configured for this dataset, configure it first")
        run([darknet['path'], *args, *darknet['options']])

    def list_experiments(self):
        return [Experiment(self, e) for e in self.config['experiments'].keys()]

    def get_experiment(self, name):
        if name is None:
            return next(e for e in self.list_experiments() if e.config['default'])
        else:
            return Experiment(self, name)

    def get_real(self, subset=None):
        '''Returns a generator that yields all real annotations, or only those
        in a given subset.'''
        if subset is None:
            pattern = '**/*.png'
        else:
            pattern = subset+'/*.png'
        return (Transcription(file) for file in
                (self.path / 'real').glob(pattern))

    def get_generated(self):
        '''Returns a generator that yields all generated annotations'''
        return (Transcription(file) for file in
                (self.path / 'generated').glob('*.png'))

    def get_symbols(self):
        '''Returns a generator for all the symbols.'''
        return (Transcription(file) for file in
                (self.path / 'symbols').glob('*.png'))

    def __getattr__(self, attr):
        if attr == 'path':
            if not self._path.exists():
                raise SystemExit("Dataset '{}' does not exist".format(self._path))
            self.path = self._path
            return self.path
        if attr == 'config':
            if not self.config_path.exists():
                raise SystemExit("Path '{}' is not a valid dataset".format(self._path))
            self.config = toml.loads(self.config_path.read_text())
            return self.config


@click.command()
@click.pass_context
def create(ctx):
    ''' Creates a dataset directory with the correct structure.'''
    dataset = ctx.obj['dataset']

    dataset.create()
    path = dataset.path

    title = click.prompt("Title of the dataset")
    description = click.prompt("Description of the dataset")

    default_config = Template((Path(__file__).parent / 'default_config.toml').read_text())
    dataset.config_path.write_text(default_config.substitute(
        title=title, description=description))

    click.secho("Created dataset '{}' at '{}'\n" .format(title, path), bold=True)
    click.echo("Configuration can be found in 'config.toml'. We recommend \n"
                "reading it now and adapting it to this dataset, but you can \n"
                "always do it later or use the command `config`.")
    if click.confirm("View config file now?", default=True):
        ctx.invoke(config_edit)


def style(condition, right, wrong=None):
    color = "green" if condition else "red"
    text = right if (condition or (wrong is None)) else wrong
    return click.style(str(text), fg=color)


@click.command()
@click.pass_obj
@click.option('--image_dir', '-i', multiple=True, type=click.Path(exists=True),
              required=True, help="Directory from which to import images")
@click.option('--name', '-n', default='default',
              help="Name for the subset of the dataset where to import the images")
def add_images(obj, image_dir, name):
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
            new_trans.create_from(image=img)
            idx = idx + 1
            num = num + 1
        click.echo("imported {}".format(style(num > 0, num)))
    click.echo("\n")


@click.command()
@click.option('--train_percentage', '-t', type=click.IntRange(0, 100), default=60)
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
    config = dataset.config
    click.secho('{}\n{}'.format(config["title"], '▔' * len(config['title'])), bold=True)
    click.echo(config["description"])
    click.secho('Tag schema: {}\n'.format(', '.join(config["tag_schema"])), bold=True)

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

    dn_binary = (dataset.config.get('darknet', {}).get('path'))
    click.echo('Darknet {} properly configured in config.toml'.format(
        style(dn_binary is not None and Path(dn_binary).exists(), 'is', 'is not')))

    exps = dataset.list_experiments()
    if len(exps) > 1:
        click.echo('\nExperiments:')
        for e in exps:
            click.echo('- {}: {}'.format(e.name, e.config['subject']))

    experiment = dataset.get_experiment(obj['experiment'])

    header = "Experiment: '{}'".format(experiment.name)
    click.secho("\n{}\n{}".format(header, '▔' * len(header)), bold=True)
    click.echo("{}\n".format(experiment.config['subject']))

    darknet = experiment.path / 'darknet.cfg'
    num_txt = sum(1 for r in real if r._txt.exists()) + count(gen.glob('*.txt'))
    click.echo('Dataset {} ready for training'.format(style(
        darknet.exists() and num_txt == num_gen + num_real,
        'is', "is not")))

    click.echo('Neural network {}'.format(style(experiment.is_trained(),
               'has been trained', "hasn't been trained")))

    click.echo('')


@click.command()
@click.option('--editor', '-e', help="Editor to use instead of the automatically detected one")
@click.pass_obj
def config_edit(obj, editor):
    ''' Edit dataset configuration file (config.toml).'''
    dataset = obj['dataset']
    info = dataset.config # Ensure valid dataset
    click.edit(filename=str(dataset.config_path), editor=editor)
