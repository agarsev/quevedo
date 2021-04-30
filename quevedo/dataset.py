# 2020-04-09 Antonio F. G. Sevilla <afgs@ucm.es>

import click
from itertools import chain
from os import listdir
from pathlib import Path
import random
from string import Template
from subprocess import run
import toml

from quevedo.network import create_network
from quevedo.annotation import Target, Logogram, Grapheme


class Dataset:
    ''' Class representing a SW dataset'''

    def __init__(self, path):
        '''We lazy load the dataset path to allow the "create" command to create the
        directory but other commands to fail if it doesn't exist. This is due to how
        click works, and unlikely to be fixed. '''
        self._path = Path(path)
        self.logogram_path = self._path / 'logograms'
        self.grapheme_path = self._path / 'graphemes'
        self.config_path = self._path / 'config.toml'
        self.script_path = self._path / 'scripts'

    def create(self):
        p = self._path
        if p.exists() and len(listdir(p)) > 0:
            raise SystemExit("Directory '{}' not empty, aborting".format(p.resolve()))
        self.path = p
        (self.logogram_path).mkdir(parents=True)
        (self.grapheme_path).mkdir()
        (self.path / 'networks').mkdir()

    def run_darknet(self, *args):
        darknet = self.config.get('darknet')
        if darknet is None:
            raise SystemExit("Darknet not configured for this dataset, configure it first")
        run([darknet['path'], *args, *darknet['options']])

    def list_networks(self):
        return [create_network(self, n) for n in self.config['network'].keys()]

    def get_network(self, name):
        if name is None:
            return next(n for n in self.list_networks() if n.config['default'])
        else:
            return create_network(self, name)

    def get_single(self, target: Target, subset, id):
        if target == Target.LOGO:
            return Logogram(self.logogram_path / subset / id)
        elif target == Target.GRAPH:
            return Grapheme(self.grapheme_path / subset / id)
        else:
            raise ValueError('A single target is needed')

    def new_single(self, target: Target, subset, **kwds):
        if target == Target.LOGO:
            path = self.logogram_path / subset
            next_id = sum(1 for _ in path.glob('*.png')) + 1
            a = Logogram(path / str(next_id)).create_from(**kwds)
        elif target == Target.GRAPH:
            path = self.grapheme_path / subset
            next_id = sum(1 for _ in path.glob('*.png')) + 1
            a = Grapheme(path / str(next_id)).create_from(**kwds)
        else:
            raise ValueError('A single target is needed')
        return a

    def get_annotations(self, target: Target, subset=None):
        '''Returns a generator that yields all annotations, those of a given
        target, or only those in a given subset (or subsets) and target.'''
        if subset is None or len(subset) == 0:
            if Target.LOGO in target:
                ret = (Logogram(file) for file in
                       self.logogram_path.glob('**/*.png'))
                if Target.GRAPH in target:
                    ret = chain(ret, (Grapheme(file) for file in
                       self.grapheme_path.glob('**/*.png')))
                return ret
            elif Target.GRAPH in target:
                return (Grapheme(file) for file in
                       self.grapheme_path.glob('**/*.png'))
            else:
                raise ValueError('A target needs to be specified')
        elif isinstance(subset, str):
            if target == Target.LOGO:
                return (Logogram(file) for file in
                        (self.logogram_path / subset).glob('*.png'))
            elif Target.GRAPH in target:
                return (Grapheme(file) for file in
                        (self.grapheme_path / subset).glob('*.png'))
            else:
                raise ValueError('If a subset is specified, a single target is needed')
        else:
            return chain(*(self.get_annotations(target, d) for d in subset))

    def get_subsets(self, target: Target):
        '''Gets information about the subsets in a given target.'''
        if target == Target.LOGO:
            path = self.logogram_path
        elif target == Target.GRAPH:
            path = self.grapheme_path
        else:
            raise ValueError('A single target is needed')
        return [{'name': d.stem,
                 'count': sum(1 for _ in d.glob('*.png'))}
                for d in path.glob('*') if d.is_dir()]

    def create_subset(self, target: Target, name, existing='a'):
        '''Creates the directory for a new subset. If it exists, behaviour is
        controlled by `existing`. It can be 'a' to abort (the default), 'r' to
        remove existing annotations, or 'm' (merge) to do nothing. Returns the
        creeated path.'''
        if target == Target.LOGO:
            path = self.logogram_path / name
        elif target == Target.GRAPH:
            path = self.grapheme_path / name
        else:
            raise ValueError('A single target is needed')
        try:
            path.mkdir()
        except FileExistsError:
            if existing is None:
                existing = click.prompt("Target directory already exists.\n"
                    "What to do? (m)erge/(r)eplace/(a)bort", default='a')[0]
            if existing == 'r':
                for f in path.glob('*'):
                    f.unlink()
            elif existing == 'm':
                pass
            else:
                raise click.Abort()
        return path

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
@click.option('--grapheme-set', '-g', help="Import the images to this grapheme set.")
@click.option('--logogram-set', '-l', help="Import the images to this logogram set.")
@click.option('-m', '--merge', 'existing', flag_value='m',
              help='''Merge new images with existing ones, if any.''')
@click.option('-r', '--replace', 'existing', flag_value='r',
              help='''Replace old images with new ones, if any.''')
def add_images(obj, image_dir, grapheme_set, logogram_set, existing):
    ''' Import images from directories to a dataset.'''
    dataset = obj['dataset']

    if grapheme_set is not None:
        if logogram_set is not None:
            raise click.UsageError("Please choose either a logogram or a grapheme set name")
        dest = grapheme_set
        target = Target.GRAPH
    elif logogram_set is not None:
        dest = logogram_set
        target = Target.LOGO
    else:
        raise click.UsageError("Please choose either a logogram or a grapheme set name")

    dest_dir = dataset.create_subset(target, dest, existing)

    for d in image_dir:
        click.echo("Importing images from '{}' to '{}'...".format(
            d, dest_dir), nl=False)
        num = 0
        for img in Path(d).glob('*.png'):
            dataset.new_single(target, dest, image_path=img)
            num = num + 1
        click.echo("imported {}".format(style(num > 0, num)))
    click.echo("\n")


@click.command()
@click.option('--grapheme-set', '-g', multiple=True, help="Grapheme set(s) to split.")
@click.option('--logogram-set', '-l', multiple=True, help="Logogram set(s) to split.")
@click.option('--percentage', '-p', type=click.IntRange(0, 100), default=60)
@click.option('--seed', type=click.INT, help='A seed for the random split algorithm.')
@click.pass_obj
def train_test_split(obj, grapheme_set, logogram_set, percentage, seed):
    '''Split annotation files in the given subsets into two sets, one for
    training and one for test, in the given subsets. This split will not be done
    physically but rather as a mark on the annotation file.

    If no subsets are given, all annotations will be marked. If homogeneous
    split is required, call this command once for each set.'''
    dataset = obj['dataset']

    random.seed(seed)

    if len(grapheme_set) > 0:
        if len(logogram_set) > 0:
            raise click.UsageError("Grapheme and logogram sets can't be split "
                                   "at the same time")
        an = list(dataset.get_annotations(Target.GRAPH, grapheme_set))
    elif len(logogram_set) > 0:
        an = list(dataset.get_annotations(Target.LOGO, logogram_set))
    else:
        raise click.UsageError("Either grapheme or logogram sets to split are required")

    random.shuffle(an)
    split_point = round(len(an) * percentage / 100)

    for t in an[:split_point]:
        t.set = 'train'
        t.save()

    for t in an[split_point:]:
        t.set = 'test'
        t.save()

    click.echo("Dataset split into train ({} files) and test ({} files)".format(
               split_point, len(an) - split_point))


def count(l):
    return sum(1 for _ in l)


@click.command()
@click.pass_obj
def info(obj):
    ''' Returns status information about a dataset.'''
    dataset: Dataset = obj['dataset']

    path = dataset.path
    config = dataset.config
    click.secho('{}\n{}'.format(config["title"], '▔' * len(config['title'])),
                nl=False, bold=True)
    click.echo(config["description"])
    click.secho('Tag schema: {}\n'.format(', '.join(config["tag_schema"])), bold=True)

    logos = list(dataset.get_annotations(Target.LOGO))
    num_logos = count(logos)
    click.echo('Logograms: {}'.format(style(num_logos > 0, num_logos)))
    click.echo('Subsets: {}'.format(
        ', '.join(s['name'] for s in dataset.get_subsets(Target.LOGO))))
    num_annot = sum(len(t.graphemes) > 0 for t in logos)
    click.echo('Annotated: {}/{}'.format(
        style(num_annot == num_logos, num_annot), num_logos))

    graphemes = list(dataset.get_annotations(Target.GRAPH))
    num_graph = count(graphemes)
    click.echo('\nGraphemes: {}'.format(style(num_graph > 0, num_graph)))
    click.echo('Subsets: {}'.format(
        ', '.join(s['name'] for s in dataset.get_subsets(Target.GRAPH))))
    num_annot = sum(len(s.tags) > 0 for s in graphemes)
    click.echo('Annotated: {}/{}'.format(
        style(num_annot == num_graph, num_annot), num_graph))

    dn_binary = (dataset.config.get('darknet', {}).get('path'))
    click.echo('\nDarknet {} properly configured in config.toml'.format(
        style(dn_binary is not None and Path(dn_binary).exists(), 'is', 'is not')))

    nets = dataset.list_networks()
    if len(nets) > 1:
        click.echo('\nNetworks:')
        for n in nets:
            click.echo('- {}: {}'.format(n.name, n.config['subject']))

    net = dataset.get_network(obj['network'])

    header = "Network: '{}'".format(net.name)
    click.secho("\n{}\n{}".format(header, '▔' * len(header)), bold=True)
    click.echo("{}\n".format(net.config['subject']))

    click.echo('The network {} ready for training'.format(style(
        net.is_prepared(), 'is', "is not")))

    click.echo('The network {}'.format(style(
        net.is_trained(), 'has been trained', "hasn't been trained")))

    click.echo('')


@click.command()
@click.option('--editor', '-e', help="Editor to use instead of the automatically detected one")
@click.pass_obj
def config_edit(obj, editor):
    ''' Edit dataset configuration file (config.toml).'''
    dataset = obj['dataset']
    info = dataset.config # Ensure valid dataset
    click.edit(filename=str(dataset.config_path), editor=editor)
