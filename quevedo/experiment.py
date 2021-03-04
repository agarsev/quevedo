# 2020-10-08 Antonio F. G. Sevilla <afgs@ucm.es>

from itertools import chain
from pathlib import Path
from string import Template


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

        try:
            self._tag_index = dataset.config['tag_schema'].index(self.config['tag'])
        except ValueError:
            raise SystemExit("Tag '{}' for experiment '{}' does not exist"
                             " in the dataset".format(self.config['tag'], name))

    def get_tag(self, symbol_tags):
        '''Get the actual tag for this experiment from the list of annotated
        tags of a symbol.'''
        try:
            return symbol_tags[self._tag_index]
        except IndexError:
            return None

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

    def get_train_files(self):
        task = self.config['task']
        if task == 'detect':
            all_annotation_files = self.dataset.get_real()
            if self.config['generate']:
                all_annotation_files = chain(all_annotation_files, self.dataset.get_generated())
            return [t for t in all_annotation_files if t.anot.get('set') == 'train']
        if task == 'classify':
            return [s for s in self.dataset.get_symbols()]

    def prepare(self):
        ''' Creates the files needed for training and testing darknet on this dataset and
        experiment.'''

        task = self.config['task']
        annotation_files = self.get_train_files()

        # Collect all symbol names/classes (1st pass)
        symbols = set()
        for t in annotation_files:
            if task == 'detect':
                symbols |= set(self.get_tag(s['tags'])
                               for s in t.anot['symbols'])
            elif task == 'classify':
                symbols.add(self.get_tag(t.anot['tags']))
        # (we need two passes to get a sorted, and thus predictable, symbol list)
        symbols = sorted(symbols)
        num_classes = len(symbols)

        names_file = self.path / 'obj.names'
        names_file.write_text("\n".join(symbols) + "\n")

        # Write darknet/yolo bounding box files (2nd pass)
        for t in annotation_files:
            if task == 'detect':
                t._txt.write_text("".join("{} {} {} {} {}\n".format(
                    symbols.index(self.get_tag(s['tags'])), *s['box'])
                    for s in t.anot['symbols']))
            elif task == 'classify':
                t._txt.write_text("{}\n".format(self.get_tag(t.anot['tags'])))

        # Write train file with the list of files to train on, that is real +
        # generated transcriptions
        train_file = self.path / 'train.txt'
        train_file.write_text("\n".join(str(f.image.resolve())
                                        for f in annotation_files) + "\n")

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

        # Write net configuration. See the darknet.cfg file provided from upstream,
        # the template is filled in here.
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
            net_config = template.substitute(num_classes=num_classes)
            (self.path / 'darknet.cfg').write_text(net_config)
