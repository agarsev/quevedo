# 2020-10-08 Antonio F. G. Sevilla <afgs@ucm.es>

from itertools import chain
from os import symlink
from pathlib import Path
from shutil import rmtree
from string import Template

from quevedo.annotation import Target


class Experiment:
    ''' Class representing an experiment part of a dataset.'''

    def __init__(self, dataset, name):
        self.name = name
        self.dataset = dataset
        try:
            self.config = dataset.config['experiments'][name]
        except ValueError:
            raise SystemExit("No such experiment: {}".format(name))

        self.path = dataset.path / 'experiments' / name
        self.path.mkdir(exist_ok=True)

        if 'tag' not in self.config:
            self._tag_index = 0
        else:
            try:
                self._tag_index = dataset.config['tag_schema'].index(self.config['tag'])
            except ValueError:
                raise SystemExit("Tag '{}' for experiment '{}' does not exist"
                                 " in the dataset".format(self.config['tag'], name))

    def get_tag(self, grapheme_tags):
        '''Get the actual tag for this experiment from the list of annotated
        tags of a grapheme.'''
        try:
            return grapheme_tags[self._tag_index]
        except IndexError:
            return None

    def is_prepared(self):
        '''Checks whether the experiment's neural network has been trained and
        can be used to predict.'''
        darknet = self.path / 'darknet.cfg'
        return darknet.exists()

    def is_trained(self):
        '''Checks whether the experiment's neural network has been trained and
        can be used to predict.'''
        weights = self.path / 'darknet_final.weights'
        return weights.exists()

    def get_network_type(self):
        task = self.config['task']
        if task == 'detect':
            return 'detector'
        elif task == 'classify':
            return 'classifier'
        else:
            raise SystemExit("Unsupported task for experiment {}: {}".format(
                self.name, task))

    def get_annotations(self, set='train'):
        task = self.config['task']
        subsets = self.config.get('subsets')
        if task == 'classify':
            target = Target.GRAPH
        else:
            target = Target.LOGO
        if subsets is None:
            annotations = self.dataset.get_annotations(target)
        else:
            annotations = (self.dataset.get_annotations(target, s) for s in subsets)
        return [a for a in annotations if a.anot.get('set') == set]

    def prepare(self):
        ''' Creates the files needed for training and testing darknet on this dataset and
        experiment.'''

        task = self.config['task']
        annotations = self.get_annotations('train')

        train_path = self.path / 'train'
        if task == 'classify':
            try:
                train_path.mkdir()
            except FileExistsError:
                rmtree(train_path)
                train_path.mkdir()

        # Collect all graphemes names/classes (1st pass)
        graphemes = set()
        for t in annotations:
            if task == 'detect':
                graphemes |= set(self.get_tag(s['tags'])
                               for s in t.anot['graphemes'])
            elif task == 'classify':
                graphemes.add(self.get_tag(t.anot['tags']))
        # (we need two passes to get a sorted, and thus predictable, grapheme list)
        graphemes = sorted(graphemes)
        num_classes = len(graphemes)

        names_file = self.path / 'obj.names'
        names_file.write_text("\n".join(graphemes) + "\n")

        # (2nd pass)
        train_file = self.path / 'train.txt'
        train_fd = open(train_file, 'w')
        num = 0
        for t in annotations:
            if task == 'detect':
                # Write darknet/yolo bounding box files
                t._txt.write_text("".join("{} {} {} {} {}\n".format(
                    graphemes.index(self.get_tag(s['tags'])), *s['box'])
                    for s in t.anot['graphemes']))
                train_fd.write("{}\n".format(t.image.resolve()))
            elif task == 'classify':
                # Symlink annotation with correct name
                num = num + 1
                link_name = (train_path / "{}_{}.png".format(
                    self.get_tag(t.anot['tags']), num)).resolve()
                symlink(t.image.resolve(), link_name)
                train_fd.write("{}\n".format(link_name))
        train_fd.close()

        # In this directory, the weights of the trained network will be stored
        weight_d = self.path / 'weights'

        names_file_name = 'names'
        if task == 'classify':
            names_file_name = 'labels'

        # Write meta-configuration information in the darknet data file
        (self.path / 'darknet.data').write_text(("classes = {}\n"
            "train = {}\n{} = {}\nbackup = {}\n").format(
                num_classes, train_file.resolve(),
                names_file_name,
                names_file.resolve(), weight_d.resolve()))

        # Write net configuration. See the cfg template file provided from upstream
        if task == 'detect':
            num_max_batches = num_classes * 2000
            template = Template((Path(__file__).parent / 'darknet/yolo.cfg').read_text())
            net_config = template.substitute(
                num_classes=num_classes,
                num_filters=((num_classes + 5) * 3),
                num_max_batches=num_max_batches,
                num_steps_1=int(num_max_batches * 80 / 100),
                num_steps_2=int(num_max_batches * 90 / 100))
            (self.path / 'darknet.cfg').write_text(net_config)
        if task == 'classify':
            num_max_batches = num_classes * 2000
            template = Template((Path(__file__).parent / 'darknet/alexnet.cfg').read_text())
            net_config = template.substitute(
                num_classes=num_classes,
                num_max_batches=num_classes * 500,  # maybe?
                num_connected=num_classes * 10)  # Read somewhere how to choose these params
            (self.path / 'darknet.cfg').write_text(net_config)
