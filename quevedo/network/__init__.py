# 2021-04-21 Antonio F. G. Sevilla <afgs@ucm.es>


from .detect import DetectNet
from .classify import ClassifyNet


def create_network(dataset, name):
    config = dataset.config['network'][name]
    if config['task'] == 'detect':
        return DetectNet(dataset, name)
    elif config['task'] == 'classify':
        return ClassifyNet(dataset, name)
    raise ValueError('Unknown task {} for network {}'.format(
        config['task'], name))
