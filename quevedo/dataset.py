# 2020-04-09 Antonio F. G. Sevilla <afgs@ucm.es>
# Licensed under the Open Software License version 3.0

import click
from itertools import chain
from os import listdir
from pathlib import Path
from string import Template
from subprocess import run
import toml

from quevedo.annotation import Target, Logogram, Grapheme
from quevedo.network import create_network
from quevedo.pipeline import create_pipeline


CURRENT_CONFIG_VERSION = 2


class Dataset:
    '''Class representing a Quevedo dataset.

    It provides access to the annotations, subsets, and any neural networks
    contained.

    Args:
        path: the path to the dataset directory (existing or to be created)
    '''

    # We lazy load the dataset path to allow the "create" command to create the
    # directory but other commands to fail if it doesn't exist. This is due to
    # how click works, and unlikely to be fixed.
    def __init__(self, path='.'):
        self._path = Path(path)
        self.logogram_path = self._path / 'logograms'
        self.grapheme_path = self._path / 'graphemes'
        self.config_path = self._path / 'config.toml'
        self.local_config_path = self._path / 'config.local.toml'
        self.script_path = self._path / 'scripts'
        self._networks = {}
        self._pipelines = {}

    @property
    def path(self):
        '''pathlib.Path: Path to the dataset directory.'''
        if not hasattr(self, '_checked_path'):
            if not self._path.exists():
                raise SystemExit("Dataset '{}' does not exist".format(self._path))
            self._checked_path = self._path
        return self._checked_path

    @property
    def config(self):
        '''dict: [Dataset configuration](config.md)'''
        if not hasattr(self, '_config'):
            if not self.config_path.exists():
                raise SystemExit("Path '{}' is not a valid dataset".format(self._path))
            self._config = toml.loads(self.config_path.read_text())
            version = self._config.get('config_version', 0)
            if version != CURRENT_CONFIG_VERSION:
                raise SystemExit("Dataset '{}' uses an outdated configuration version ({}).\n"
                                 "Please use the 'migrate' command to update.".format(
                                     self._path, version))
            if self.local_config_path.exists():
                self._config = _dict_merge(self._config, toml.loads(self.local_config_path.read_text()))
        return self._config

    def get_config(self, section, key):
        '''Get the configuration for a key under a section (a value in a table,
        eg [network.example], where network is the section and example is the
        key. This method looks for the "extend" key and merges configuration
        recursively.

        Returns:
            dict
        '''
        config = {}
        while key is not None:
            try:
                ext = self.config[section][key]
                key = ext.get('extend')
            except KeyError:
                raise ValueError("No such {}: {}".format(section, key)) from None
            config = _dict_merge(ext, config)  # Newer keys (config) have precedence
        try:
            del config['extend']
        except KeyError:
            pass
        return config

    def create(self):
        '''Create or initialize a directory to be a Quevedo dataset.'''
        p = self._path
        if p.exists() and len(listdir(p)) > 0:
            raise SystemExit("Directory '{}' not empty, aborting".format(p.resolve()))
        (self.logogram_path).mkdir(parents=True)
        (self.grapheme_path).mkdir()
        (self.path / 'networks').mkdir()

    def run_darknet(self, *args):
        darknet = self.config.get('darknet')
        if darknet is None:
            raise SystemExit("Darknet not configured for this dataset, configure it first")
        run([darknet['path'], *args, *darknet['options']])

    def list_networks(self):
        '''Get a list of all neural networks for this dataset.

        Returns:
            list of [Networks](#network)'''
        if 'network' not in self.config:
            return []
        return [create_network(self, n) for n in self.config['network'].keys()]

    def get_network(self, name):
        '''Get a single neural network by name.

        Args:
            name: name of the neural network as specified in the configuration file.

        Returns:
            a [Network](#quevedonetworknetworknetwork) object.
        '''
        try:
            return self._networks[name]
        except KeyError:
            pass
        ret = create_network(self, name)
        self._networks[name] = ret
        return ret

    def list_pipelines(self):
        '''Get a list of all pipelines for this dataset.

        Returns:
            list of [Pipelines](#pipeline)'''
        if 'pipeline' not in self.config:
            return []
        return [create_pipeline(self, p) for p in self.config['pipeline'].keys()]

    def get_pipeline(self, name):
        '''Get a pipeline by name.

        Args:
            name: name of the pipeline as specified in the configuration file.

        Returns:
            a [Pipeline](#quevedopipelinepipeline) object.
        '''
        try:
            return self._pipelines[name]
        except KeyError:
            pass
        ret = create_pipeline(self, name)
        self._pipelines[name] = ret
        return ret

    def get_single(self, target: Target, subset, id):
        '''Retrieve a single annotation.

        Args:
            target: [Target](#annotations) (type) of the annotation to retrieve.
            subset: name of the subset where the annotation is stored.
            id: number of the annotation in the subset.

        Returns:
            a single [Annotation](#annotation) of the appropriate type.
        '''
        if target == Target.LOGO:
            return Logogram(self.logogram_path / subset / id)
        elif target == Target.GRAPH:
            return Grapheme(self.grapheme_path / subset / id)
        else:
            raise ValueError('A single target is needed')

    def new_single(self, target: Target, subset, **kwds):
        '''Create a new annotation.

        This method creates the annotation files in the corresponding directory,
        and initializes them with
        [`create_from`](#quevedo.annotation.annotation.Annotation.create_from).
        Any extra arguments will be passed to that method.

        Args:
            target: [Target](#annotations) (type) of the annotation to create.
            subset: name of the (existing) subset where to place it.

        Returns:
            the new [Annotation](#annotation).
        '''
        if target == Target.LOGO:
            path = self.logogram_path / subset
            path.mkdir(exist_ok=True)
            next_id = sum(1 for _ in path.glob('*.png')) + 1
            a = Logogram(path / str(next_id)).create_from(**kwds)
        elif target == Target.GRAPH:
            path = self.grapheme_path / subset
            path.mkdir(exist_ok=True)
            next_id = sum(1 for _ in path.glob('*.png')) + 1
            a = Grapheme(path / str(next_id)).create_from(**kwds)
        else:
            raise ValueError('A single target is needed')
        return a

    def get_annotations(self, target: Target = Target.GRAPH | Target.LOGO, subset=None):
        '''Get annotations from the dataset.

        Depending on the arguments, all annotations, those of a given
        target, or only those in a given subset (or subsets) and target will be
        selected.

        Args:
            target: [Target](#annotations) (type) of the annotations to
                retrieve. By default, it is the union of both types, so all
                annotations are retrieved: `Target.GRAPH | Target.LOGO`.
            subset: name of the subsets to get, or `None` to get annotations from
                all subsets.

        Returns:
            a generator that yields selected annotations.
        '''
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
        '''Gets information about subsets in the dataset.

        Args:
            target: [Target](#annotations) (type) of the annotation subsets.

        Returns:
            a sorted list of `dict`, each with the keys `name` for the name of
            the subset, and `count` for the number of annotations in it.
        '''
        if target == Target.LOGO:
            path = self.logogram_path
        elif target == Target.GRAPH:
            path = self.grapheme_path
        else:
            raise ValueError('A single target is needed')
        return sorted(({'name': d.stem,
                        'count': sum(1 for _ in d.glob('*.png'))}
                       for d in path.glob('*') if d.is_dir()),
                      key=lambda s: s['name'])

    def create_subset(self, target: Target, name, existing='a'):
        '''Creates the directory for a new subset.

        Args:
            target: [Target](#annotations) (type) of the annotation subset to create.
            name: name for the new subset.
            existing: controls behaviour when the directory already exists.  It
                can be 'a' to abort (the default), 'r' to remove existing
                annotations, or 'm' (merge) to do nothing.

        Returns:
            the path of the created directory.
        '''
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

    def is_train(self, annotation):
        '''Checks if an annotation belongs to the training split.'''
        return annotation.fold in self.config['train_folds']

    def is_test(self, annotation):
        '''Checks if an annotation belongs to the training split.'''
        return annotation.fold in self.config['test_folds']


def _dict_merge(a, b):
    '''Recursively merge keys from dict b into a. Keys in b override those in a.'''
    r = {}
    for k in chain(a.keys(), b.keys()):
        if k in a and k in b and isinstance(a[k], dict) and isinstance(b[k], dict):
            r[k] = _dict_merge(a[k], b[k])
        elif k in b:
            r[k] = b[k]
        else:
            r[k] = a[k]
    return r


@click.command('create')
@click.pass_context
def create(ctx):
    '''Create and initialize a Quevedo dataset.'''
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


@click.command('add_images')
@click.pass_obj
@click.option('--image_dir', '-i', multiple=True, type=click.Path(exists=True),
              required=True, help="Directory from which to import images.")
@click.option('--grapheme-set', '-g', help="Import the images to this grapheme set.")
@click.option('--logogram-set', '-l', help="Import the images to this logogram set.")
@click.option('-m', '--merge', 'existing', flag_value='m',
              help='''Merge new images with existing ones, if any.''')
@click.option('-r', '--replace', 'existing', flag_value='r',
              help='''Replace old images with new ones, if any.''')
@click.option('--sort-numeric', 'sort', flag_value='1',
              help="Sort images ids by filename (numeric).")
@click.option('--sort-alphabetic', 'sort', flag_value='a',
              help="Sort images ids by filename (alphabetic).")
@click.option('--no-sort', 'sort', flag_value='n',
              help="Don't sort images to import.  [default]")
def add_images(obj, image_dir, grapheme_set, logogram_set, existing, sort):
    '''Import images from external directories into the dataset.

    For now, images need to be in the PNG format, and have 3 channels (color)
    and 8 bit depth.'''
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
        sources = Path(d).glob('*.png')
        if sort == 'a':
            sources = sorted(sources)
        elif sort == '1':
            sources = sorted(sources, key=lambda fn: int(fn.stem))
        for img in sources:
            dataset.new_single(target, dest, image_path=img)
            num = num + 1
        click.echo("imported {}".format(style(num > 0, num)))
    click.echo("\n")


def count(l):
    return sum(1 for _ in l)


@click.command('info')
@click.pass_obj
def info(obj):
    '''Get general status information about a dataset.'''
    dataset: Dataset = obj['dataset']

    config = dataset.config
    click.secho('{}\n{}'.format(config["title"], '▔' * len(config['title'])),
                nl=False, bold=True)
    click.echo(config["description"])
    click.secho('Grapheme tag schema: {}'.format(', '.join(config["g_tags"])))
    click.secho('Logogram tag schema: {}'.format(', '.join(config["l_tags"])))
    click.secho('Edge tag schema: {}'.format(', '.join(config["e_tags"])))
    click.secho('Meta tags for annotations: {}\n'.format(', '.join(config["meta_tags"])))

    logos = list(dataset.get_annotations(Target.LOGO))
    num_logos = count(logos)
    click.echo('Logograms: {}'.format(style(num_logos > 0, num_logos)))
    click.echo('Subsets: {}'.format(
        ', '.join(s['name'] for s in dataset.get_subsets(Target.LOGO))))
    num_annot = sum(len(t.graphemes) > 0 for t in logos)
    click.echo('Annotated: {}/{}'.format(
        style(num_annot == num_logos, num_annot), num_logos))

    graphemes = list(dataset.get_annotations(Target.GRAPH))  # type: list[Grapheme]
    num_graph = count(graphemes)
    click.echo('\nGraphemes: {}'.format(style(num_graph > 0, num_graph)))
    click.echo('Subsets: {}'.format(
        ', '.join(s['name'] for s in dataset.get_subsets(Target.GRAPH))))
    num_annot = sum(len(s.tags.keys()) > 0 for s in graphemes)
    click.echo('Annotated: {}/{}'.format(
        style(num_annot == num_graph, num_annot), num_graph))

    dn_binary = (dataset.config.get('darknet', {}).get('path'))
    click.echo('\nDarknet {} properly configured in config.toml'.format(
        style(dn_binary is not None and Path(dn_binary).exists(), 'is', 'is not')))

    nets = dataset.list_networks()
    if len(nets) > 1:
        click.echo('\nNetworks:')
        for n in nets:
            click.echo('- {}: {}'.format(n.name, n.config.get('subject', '')))

    pipes = dataset.list_pipelines()
    if len(pipes) > 1:
        click.echo('\nPipelines:')
        for p in pipes:
            click.echo('- {}: {}'.format(p.name, p.config.get('subject', '')))

    if 'network' in obj:
        net = dataset.get_network(obj['network'])

        header = "Network: '{}'".format(net.name)
        click.secho("\n{}\n{}".format(header, '▔' * len(header)), bold=True)
        click.echo("{}\n".format(net.config['subject']))

        click.echo('The network {} ready for training'.format(style(
            net.is_prepared(), 'is', "is not")))

        click.echo('The network {}'.format(style(
            net.is_trained(), 'has been trained', "hasn't been trained")))

    # TODO: add info about the pipeline

    click.echo('')


@click.command('config')
@click.option('--editor', '-e', help="Editor to use instead of the automatically detected one")
@click.pass_obj
def config_edit(obj, editor):
    '''Edit dataset configuration.

    This command is a simple convenience to launch an editor open at the
    configuration file (config.toml).'''
    dataset = obj['dataset']
    _ = dataset.config  # Ensure valid dataset
    click.edit(filename=str(dataset.config_path), editor=editor)
