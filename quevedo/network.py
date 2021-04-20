# 2020-10-08 Antonio F. G. Sevilla <afgs@ucm.es>

from itertools import chain
import json
from os import symlink
from pathlib import Path
from shutil import rmtree
from string import Template

from quevedo.annotation import Target


class Network:
    ''' Class representing a neural net to train and predict logograms or
    graphemes.'''

    def __init__(self, dataset, name):
        self.name = name
        self.dataset = dataset
        try:
            self.config = dataset.config['network'][name]
        except ValueError:
            raise SystemExit("No such network: {}".format(name))

        self.path = dataset.path / 'networks' / name
        self.path.mkdir(exist_ok=True)

        if 'tag' not in self.config:
            self._tag_index = 0
        else:
            try:
                self._tag_index = dataset.config['tag_schema'].index(self.config['tag'])
            except ValueError:
                raise SystemExit("Tag '{}' (chosen for network '{}') does not exist"
                                 " in the dataset".format(self.config['tag'], name))

    def get_tag(self, grapheme_tags):
        '''Get the tag to use for this network from the list of annotated tags of a
        grapheme.'''
        try:
            return grapheme_tags[self._tag_index]
        except IndexError:
            return None

    def is_prepared(self):
        '''Checks whether the neural network configuration files have been
        made.'''
        darknet = self.path / 'darknet.cfg'
        return darknet.exists()

    def is_trained(self):
        '''Checks whether the neural network has been trained and can be used to
        predict.'''
        weights = self.path / 'darknet_final.weights'
        return weights.exists()

    def get_network_type(self):
        task = self.config['task']
        if task == 'detect':
            return 'detector'
        elif task == 'classify':
            return 'classifier'
        else:
            raise SystemExit("Unsupported task for network {}: {}".format(
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
            annotations = chain(*(self.dataset.get_annotations(target, s)
                                  for s in subsets))
        return [a for a in annotations if a.anot.get('set') == set]

    def prepare(self):
        ''' Creates the files needed for training and testing darknet.'''

        task = self.config['task']
        annotations = self.get_annotations('train')

        train_path = self.path / 'train'
        try:
            train_path.mkdir()
        except FileExistsError:
            rmtree(train_path)
            train_path.mkdir()

        # Collect all tags
        all_tags = set()
        for t in annotations:
            if task == 'detect':
                all_tags |= set(self.get_tag(s['tags'])
                               for s in t.anot['graphemes'])
            elif task == 'classify':
                tag = self.get_tag(t.anot['tags'])
                if tag is not None:
                    all_tags.add(tag)
        # We need a deterministic set of tags to re-use the nnet, so we sort
        # them.
        all_tags = sorted(all_tags)

        # We build a map from our tags to arbitrary labels for darknet not to
        # complain.
        tag_map = {}
        num_classes = 0
        for tag in all_tags:
            num_classes = num_classes + 1
            tag_map[tag] = 'C{:04d}'.format(num_classes)

        (self.path / 'tag_map.json').write_text(json.dumps(tag_map))

        names_file = self.path / 'obj.names'
        names_file.write_text("\n".join(tag_map.values()) + "\n")

        # Create links to the images in the train folder, with class in the name
        # in classification and an additional txt file with bounding boxes for
        # detection
        train_file = self.path / 'train.txt'
        train_fd = open(train_file, 'w')
        num = 0
        for t in annotations:
            link_name = None
            if task == 'detect':
                num = num + 1
                link_name = (train_path / "{}.png".format(num)).resolve()
                link_name.with_suffix(".txt").write_text(
                    "".join("{} {} {} {} {}\n".format(
                        # Original and arbitrary tags share index
                        all_tags.index(self.get_tag(s['tags'])),
                        *s['box'])
                        for s in t.anot['graphemes']))
            else:  # if task == 'classify':
                tag = self.get_tag(t.anot['tags'])
                if tag is None:
                    continue
                num = num + 1
                link_name = (train_path / "{}_{}.png".format(
                    tag_map[tag], num)).resolve()
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
            template = Template((Path(__file__).parent / 'darknet/alexnet.cfg').read_text())
            net_config = template.substitute(
                num_classes=num_classes,
                num_max_batches=num_classes * 50,  # maybe?
                num_connected=num_classes * 10)  # TODO: Read somewhere how to choose these params
            (self.path / 'darknet.cfg').write_text(net_config)
