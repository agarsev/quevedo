# 2021-04-21 Antonio F. G. Sevilla <afgs@ucm.es>
# Licensed under the Open Software License version 3.0


from .detect import DetectNet
from .classify import ClassifyNet


def create_network(dataset, name):
    '''Factory function to create a pipeline.'''
    config = dataset.get_config('network', name)
    if config['task'] == 'detect':
        return DetectNet(dataset, name, config)
    elif config['task'] == 'classify':
        return ClassifyNet(dataset, name, config)
    raise ValueError('Unknown task {} for network {}'.format(
        config['task'], name))
