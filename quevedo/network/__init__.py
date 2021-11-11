# 2021-04-21 Antonio F. G. Sevilla <afgs@ucm.es>
# Licensed under the Open Software License version 3.0


from .detect import DetectNet
from .classify import ClassifyNet


def create_network(dataset, name):
    try:
        config = dataset.config['network'][name]
    except KeyError:
        raise ValueError("No such network: {}".format(name))
    if 'extend' in config:
        config = {
            **dataset.config['network'][config['extend']],
            **config
        }
    if config['task'] == 'detect':
        return DetectNet(dataset, name, config)
    elif config['task'] == 'classify':
        return ClassifyNet(dataset, name, config)
    raise ValueError('Unknown task {} for network {}'.format(
        config['task'], name))
