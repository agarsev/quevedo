# 2020-10-08 Antonio F. G. Sevilla <afgs@ucm.es>

import json
import os
from pathlib import Path
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
        self.path.mkdir(exist_ok=True, parents=True)
        self._darknet = None

        if 'tag' not in self.config:
            self.get_tag = lambda tags: get_tag_by_index(tags, 0)
            self.prediction_to_tag = lambda tags, tag: update_tag(tags, 0, tag)
        else:
            tag = self.config['tag']
            tag_schema = dataset.config['tag_schema']
            try:
                if isinstance(tag, str):
                    i = tag_schema.index(tag)
                    self.get_tag = lambda tags, i=i: get_tag_by_index(tags, i)
                    self.prediction_to_tag = lambda tags, tag, i=i: update_tag(tags, i, tag)
                else:
                    i = [tag_schema.index(t) for t in self.config['tag']]
                    self.get_tag = lambda tags, i=i: get_multitag(tags, i)
                    self.prediction_to_tag = lambda tags, tag, i=i: update_multitag(tags, i, tag)
            except ValueError:
                raise SystemExit("Tag value '{}' (for network '{}') invalid".format(tag, name))

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
        annotations = self.dataset.get_annotations(self.target, subsets)
        return [a for a in annotations if a.set == set and self.filter(a)]

    def filter(self, annotation):
        '''Override to control the annotations included in training by checking
        their tags.'''
        return True

    def update_tag_set(self, tag_set, annotation):
        '''Add the relevant tag from this annotation to the tag set (used while
        collecting all tags prior to training).'''
        raise NotImplementedError

    def prepare_annotation(self, annotation, num, tag_set):
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
            num = 1
            for t in annotations:
                link_name = self.prepare_annotation(t, num, all_tags)
                if link_name is None:
                    continue
                num = num + 1
                os.symlink(t.image_path.resolve(), self.train_path / link_name)
                train_file.write("train/{}\n".format(link_name))

        # Write meta-configuration information in the darknet data file
        (self.path / 'darknet.data').write_text(("classes = {}\n"
            "train = train.txt\n{} = obj.names\nbackup = weights\n").format(
                num_classes, self.names_file_name))

        # See the cfg template files provided from upstream
        (self.path / 'darknet.cfg').write_text(
            self.get_net_config(num_classes))

    def train(self):
        '''Trains the neural network. When finished, removes partial weights and
        keeps only the last.'''
        oldcwd = os.getcwd()
        os.chdir(self.path)

        weight_d = Path('weights')
        weight_d.mkdir(exist_ok=True)

        self.dataset.run_darknet(self.network_type, 'train',
                'darknet.data', 'darknet.cfg')

        os.replace(str(weight_d / 'darknet_final.weights'),
                'darknet_final.weights')
        rmtree(str(weight_d))

        os.chdir(oldcwd)

    def load(self):
        '''Loads the weights for the trained neural network so it can be used to
        predict.'''

        if self._darknet is not None:  # Already loaded
            return

        if not (self.path / 'darknet.cfg').exists():
            raise SystemExit("Neural network has not been trained")

        if not (self.path / 'darknet_final.weights').exists():
            raise SystemExit("Neural network has not been trained")

        tag_map = json.loads((self.path / 'tag_map.json').read_text())
        self.tag_map = {v: k for k, v in tag_map.items()}

        oldcwd = os.getcwd()
        os.chdir(self.path)

        from quevedo.darknet import DarknetShutup, DarknetNetwork

        with DarknetShutup():
            self._darknet = DarknetNetwork(
                libraryPath=self.dataset.config['darknet']['library'],
                configPath='darknet.cfg',
                weightPath='darknet_final.weights',
                metaPath='darknet.data')

        os.chdir(oldcwd)

    def predict(self, image_path):
        '''Use the trained neural network to predict results from an image.'''
        raise NotImplementedError

    def test(self, annotation, stats):
        '''Use the network to get the prediction for a real annotation, compare
        results and update stats.'''
        raise NotImplementedError

    def auto_annotate(self, annotation):
        '''Use the network to annotate a real instance, possibly already
        partially annotated.'''
        raise NotImplementedError


def get_tag_by_index(tags, index):
    try:
        return tags[index]
    except IndexError:
        return None


def update_tag(tags, index, new_tag):
    while len(tags) <= index:
        tags.append(None)
    tags[index] = new_tag


def get_multitag(tags, indices):
    try:
        all_tags = (tags[i] if len(tags) > i else None for i in indices)
        all_tags = [t for t in all_tags if t is not None]
        if len(all_tags) < 1:
            return None
        else:
            return '_'.join(all_tags)
    except (IndexError, TypeError):
        return None


def update_multitag(tags, indices, result):
    for i, tag in enumerate(result.split('_')):
        update_tag(tags, indices[i], tag)
