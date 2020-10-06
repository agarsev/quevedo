# 2020-04-09 Antonio F. G. Sevilla <afgs@ucm.es>

import click
import json
from pathlib import Path
import random
from shutil import copyfile
from string import Template
from subprocess import run
import yaml


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
        exp_path = (self.path / 'experiments' / name).with_suffix('.yaml')
        if not exp_path.exists():
            raise SystemExit("No such experiment: {}".format(name))
        return yaml.safe_load(exp_path.read_text())

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
def add_images(obj, image_dir):
    ''' Import images from directories to a dataset.'''
    dataset = obj['dataset']

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
                "symbols": [],
                "set": "train",
            }))
            idx = idx + 1
            count = count + 1
        click.echo("imported {}".format(style(count > 0, count)))
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

    if seed is not None:
        random.seed(seed)

    ano_files = list((dataset.path / 'real').glob('*.json'))
    random.shuffle(ano_files)

    split_point = round(len(ano_files) * train_percentage / 100)

    for t in ano_files[:split_point]:
        ano = json.loads(t.read_text())
        ano['set'] = 'train'
        t.write_text(json.dumps(ano))

    for t in ano_files[split_point:]:
        ano = json.loads(t.read_text())
        ano['set'] = 'test'
        t.write_text(json.dumps(ano))

    click.echo("Dataset split into train ({} files) and test ({} files)".format(
               split_point, len(ano_files) - split_point))


def count(l):
    return sum(1 for _ in l)


@click.command()
@click.pass_obj
def info(obj):
    ''' Returns status information about a dataset.'''
    dataset = obj['dataset']

    path = dataset.path
    info = dataset.info
    click.secho('{}\n{}\n'.format(info["title"], '=' * len(info['title'])), bold=True)
    click.echo(info["description"])
    click.secho('Tag schema: {}\n'.format(', '.join(info["tag_schema"])), bold=True)

    real = path / 'real'
    num_real = count(real.glob('*.png'))
    click.echo('Real transcriptions: {}'.format(style(num_real > 0, num_real)))
    num_annot = sum(len(json.loads(annot.read_text())['symbols']) > 0
                    for annot in real.glob('*.json'))
    click.echo('Annotated: {}/{}\n'.format(style(num_annot == num_real, num_annot),
                                           num_real))

    exps = dataset.list_experiments()
    if len(exps) > 1:
        click.echo('Experiments:')
        for e in dataset.list_experiments():
            exp = dataset.get_experiment(e)
            click.echo('- {}: {}'.format(e, exp['subject']))

    return

    # TODO
    experiment = obj['experiment']

    if experiment is not None:

        symbols = path / 'symbols'
        num_sym = count(symbols.glob('*.png'))
        click.echo('Symbols extracted: {}'.format(style(symbols.exists(), num_sym, 'no')))

        gen = path / 'generated'
        num_gen = count(gen.glob('*.png'))
        click.echo('Transcriptions generated: {}'.format(style(gen.exists(), num_gen, 'no')))

        dn_binary = (dataset.info.get('darknet', {}).get('path'))
        click.echo('Darknet {} properly configured in info.yaml'.format(
            style(dn_binary is not None and Path(dn_binary).exists(), 'is', 'is not')))

        darknet = path / 'darknet'
        num_txt = count(real.glob('*.txt')) + count(gen.glob('*.txt'))
        click.echo('Dataset {} ready for training'.format(style(
            darknet.exists() and num_txt == num_gen + num_real,
            'is', "is not")))

        weights = path / 'weights' / 'darknet_final.weights'
        click.echo('Neural network {}'.format(style(weights.exists(),
                   'has been trained', "hasn't been trained")))

    click.echo('')
