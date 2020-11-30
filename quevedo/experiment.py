# 2020-10-08 Antonio F. G. Sevilla <afgs@ucm.es>


class Experiment:
    ''' Class representing an experiment part of a dataset.'''

    def __init__(self, dataset, name):
        self.name = name
        try:
            self.info = dataset.info['experiments'][name]
        except ValueError:
            raise SystemExit("No such experiment: {}".format(name))

        self.path = dataset.path / 'experiments' / name
        self.path.mkdir(exist_ok=True)

        try:
            self._tag_index = dataset.info['tag_schema'].index(self.info['tag'])
        except ValueError:
            raise SystemExit("Tag '{}' for experiment '{}' does not exist"
                             " in the dataset".format(self.info['tag'], name))

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
