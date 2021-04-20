# 2020-10-08 Antonio F. G. Sevilla <afgs@ucm.es>

from itertools import chain
import json
from os import symlink, replace
from shutil import rmtree


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

    def get_annotations(self, set='train'):
        subsets = self.config.get('subsets')
        if subsets is None:
            annotations = self.dataset.get_annotations(self.target)
        else:
            annotations = chain(*(self.dataset.get_annotations(self.target, s)
                                  for s in subsets))
        return [a for a in annotations if a.anot.get('set') == set]

    def update_tag_set(self, tag_set, annotation):
        '''Add the relevant tag from this annotation to the tag set (used while
        collecting all tags prior to training).'''
        raise NotImplementedError

    def prepare_annotations(self, annotation, num, tag, train_file, tag_set):
        '''Prepare the files needed to train this annotation. Return the name
        that the final file (link or copy) should have.'''
        raise NotImplementedError

    def get_net_config(self, num_classes):
        '''Get the darknet architecture (.cfg file contents) for this net.'''
        raise NotImplementedError

    def prepare(self):
        ''' Creates the files needed for training and testing darknet.'''

        annotations = self.get_annotations('train')

        self.train_path = self.path / 'train'
        try:
            self.train_path.mkdir()
        except FileExistsError:
            rmtree(self.train_path)
            self.train_path.mkdir()

        # Collect all tags and sort them to get a deterministic list
        all_tags = set()
        for t in annotations:
            self.update_tag_set(all_tags, t)
        all_tags = sorted(all_tags)

        # We build a map from our tags to arbitrary labels for darknet not to
        # complain.
        self.tag_map = {}
        num_classes = 0
        for tag in all_tags:
            num_classes = num_classes + 1
            self.tag_map[tag] = 'C{:04d}'.format(num_classes)

        (self.path / 'tag_map.json').write_text(json.dumps(self.tag_map))

        names_file = self.path / 'obj.names'
        names_file.write_text("\n".join(self.tag_map.values()) + "\n")

        # Create links to the images in the train folder, with class in the name
        # in classification and an additional txt file with bounding boxes for
        # detection
        with open(self.path / 'train.txt', 'w') as train_file:
            num = 0
            for t in annotations:
                tag = self.get_tag(t.anot['tags'])
                if tag is None:
                    continue
                num = num + 1
                link_name = self.prepare_annotation(t, num, tag, train_file,
                                                    all_tags)
                symlink(t.image.resolve(), link_name)
                train_file.write("{}\n".format(link_name))

        # In this directory, the weights of the trained network will be stored
        weight_d = self.path / 'weights'

        # Write meta-configuration information in the darknet data file
        (self.path / 'darknet.data').write_text(("classes = {}\n"
            "train = {}\n{} = {}\nbackup = {}\n").format(
                num_classes, train_file.resolve(),
                self.names_file_name,
                names_file.resolve(), weight_d.resolve()))

        # See the cfg template files provided from upstream
        (self.path / 'darknet.cfg').write_text(
            self.get_net_config(num_classes))

    def train(self):
        '''Trains the neural network. When finished, removes partial weights and
        keeps only the last.'''
        weight_d = self.path / 'weights'
        weight_d.mkdir(exist_ok=True)

        darknet_data = (self.path / 'darknet.data').resolve()
        darknet_cfg = (self.path / 'darknet.cfg').resolve()
        self.dataset.run_darknet(self.network_type, 'train', darknet_data, darknet_cfg)

        replace(str(weight_d / 'darknet_final.weights'),
                str(self.path / 'darknet_final.weights'))
        rmtree(str(weight_d))
