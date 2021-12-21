# 2020-10-08 Antonio F. G. Sevilla <afgs@ucm.es>
# Licensed under the Open Software License version 3.0

import json
import os
from pathlib import Path
from shutil import rmtree


TAG_JOIN_CHAR = ''


class Network:
    ''' Class representing a neural net to train and predict logograms or
    graphemes.'''

    def __init__(self, dataset, name, config):
        '''This method shouldn't be called directly, please use the dataset
        method [get_network](quevedodatasetdatasetget_network).'''
        #: Name of the network
        self.name = name
        #: Parent dataset
        self.dataset = dataset
        #: Configuration dictionary
        self.config = config
        #: Path to the network directory
        self.path = dataset.path / 'networks' / name
        self.path.mkdir(exist_ok=True, parents=True)

        which_tag = self.config.get('tag', dataset.config['g_tags'][0])
        try:
            if not isinstance(which_tag, str):
                def get_multitag(tags, which_tag=which_tag):
                    return TAG_JOIN_CHAR.join(tags.get(w, '') for w in which_tag)
                #: function to get the relevant label for the network from a list of tags according to `g_tags`
                self.get_tag = get_multitag

                def undo_multitag(pred, which_tag=which_tag):
                    return {which_tag[i]: val
                            for i, val in enumerate(pred.split(TAG_JOIN_CHAR))
                            if val != ''}
                #: function to get the `g_tags` values from the tag/label/class predicted by the network
                self.prediction_to_tag = undo_multitag
            elif which_tag == '':
                self.get_tag = lambda tags, which_tag=which_tag: ''
                self.prediction_to_tag = lambda pred, which_tag=which_tag: {}
            else:
                self.get_tag = lambda tags, which_tag=which_tag: tags.get(which_tag)
                self.prediction_to_tag = lambda pred, which_tag=which_tag: {which_tag: pred}
        except ValueError:
            raise SystemExit("Tag value '{}' (for network '{}') invalid".format(which_tag, name))

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

    def get_annotations(self, test=False):
        '''Get the annotations configured for use with this network.

        Args:
            test: get test annotations instead of train

        Returns:
            a list of relevant [Annotations](#annotations).
        '''
        subsets = self.config.get('subsets')
        annotations = self.dataset.get_annotations(self.target, subsets)
        correct_split = self.dataset.is_train if not test else self.dataset.is_test
        return [a for a in annotations if correct_split(a) and self._filter(a)]

    def _filter(self, annotation):
        '''Override to control the annotations included in training by checking
        their tags.'''
        return True

    def _update_tag_set(self, tag_set, annotation):
        '''Add the relevant tag from this annotation to the tag set (used while
        collecting all tags prior to training).'''
        raise NotImplementedError

    def _prepare_annotation(self, annotation, num, tag_set):
        '''Prepare the files needed to train this annotation. Return the name
        that the final file (link or copy) should have.'''
        raise NotImplementedError

    def _get_net_config(self, num_classes):
        '''Get the darknet architecture (.cfg file contents) for this net.'''
        raise NotImplementedError

    def prepare(self):
        '''Creates the files needed for training (and later using) darknet.

        Stores the files in the network directory so they can be reused or
        tracked by a version control system. Must be called before training, and
        files not deleted (except maybe the "train" directory) before
        testing or predicting with the net.'''
        annotations = self.get_annotations()

        self.train_path = self.path / 'train'
        try:
            self.train_path.mkdir()
        except FileExistsError:
            rmtree(self.train_path)
            self.train_path.mkdir()

        # Collect all tags and sort them to get a deterministic list
        all_tags = set()
        for t in annotations:
            self._update_tag_set(all_tags, t)
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
                link_name = self._prepare_annotation(t, num, all_tags)
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
            self._get_net_config(num_classes))

    def train(self, initial=None):
        '''Trains the neural network.

        When finished, removes partial weights and keeps only the last. Can be
        interrupted and optionally resumed later.

        Args:
            initial: path to the weights from which to resume training.
        '''
        oldcwd = os.getcwd()
        os.chdir(self.path)
        final = None

        weight_d = Path('weights')
        weight_d.mkdir(exist_ok=True)

        args = [self.network_type, 'train', 'darknet.data',
                'darknet.cfg']
        if initial:
            args.append(initial)

        try:
            self.dataset.run_darknet(*args)
            final = 'darknet_final.weights'
        except KeyboardInterrupt:
            final = 'darknet_last.weights'
            if not (weight_d / final).exists():
                final = None

        if final is not None:
            os.replace(str(weight_d / final), 'darknet_final.weights')
        rmtree(str(weight_d))
        os.chdir(oldcwd)

        return final

    @property
    def _darknet(self):
        '''Weights of the trained neural network'''
        if not hasattr(self, '_darknet_weights'):

            if not (self.path / 'darknet.cfg').exists():
                raise SystemExit(f"Neural network {self.name} has not been trained")

            if not (self.path / 'darknet_final.weights').exists():
                raise SystemExit(f"Neural network {self.name} has not been trained")

            tag_map = json.loads((self.path / 'tag_map.json').read_text())
            self.tag_map = {v: k for k, v in tag_map.items()}

            lib_path = Path(self.dataset.config['darknet']['library'])
            if not lib_path.is_absolute():
                lib_path = self.dataset.path / lib_path

            oldcwd = os.getcwd()
            os.chdir(self.path)

            from quevedo.darknet import DarknetNetwork

            self._darknet_weights = DarknetNetwork(
                libraryPath=str(lib_path.resolve()),
                configPath='darknet.cfg',
                weightPath='darknet_final.weights',
                metaPath='darknet.data',
                shutupDarknet=self.dataset.config['darknet'].get('shutup', True),
            )

            os.chdir(oldcwd)

        return self._darknet_weights

    def predict(self, image_path):
        '''Use the trained neural network to predict results from an image.

        Args:
            image_path: path to the image in the file system.

        Returns:
            a list of dictionaries with the predictions. Each prediction has a
            `confidence` value. Classify networks have a `tag` key for the
            predicted class, each entry is a possible classification of the
            image. Detector networks results are possible graphemes found, each
            with a `name` (predicted class) and `box` (bounding box).
            '''
        raise NotImplementedError

    def test(self, annotation, stats):
        '''Method to test the network on an annotation.

        This method is intended for internal library use, you probably want to
        use `predict` instead.

        Uses the network to get the prediction for a real annotation, compare
        results and update stats. See `test.py` for `stats`.'''
        raise NotImplementedError

    def auto_annotate(self, annotation):
        '''Use the network to automatically annotate a real instance.

        In detector networks, existing bound graphemes will be removed. In
        classify networks, tags which are not relevant to this network won't be
        modified, so it can be used incrementally.

        Args:
            annotation: [Annotation](#annotations) to automatically tag using
                this network's predictions.
        '''
        raise NotImplementedError
