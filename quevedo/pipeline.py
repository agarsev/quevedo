# 2021-11-10 Antonio F. G. Sevilla <afgs@ucm.es>
# Licensed under the Open Software License version 3.0

from quevedo import Annotation
from quevedo.run_script import module_from_file


def create_pipeline(dataset, name=None, config=None):
    '''Factory function to create a pipeline.'''
    if name is None:
        name = 'anonymous'
    else:
        try:
            config = dataset.config['pipeline'][name]
        except ValueError:
            raise ValueError("No such pipeline: {}".format(name))

    if config is None:
        raise ValueError("config is an obligatory argument if name is not None")

    if isinstance(config, list):
        return SequencePipeline(dataset, name, config)
    elif isinstance(config, str):
        if config in dataset.config['pipeline']:
            return create_pipeline(dataset, name, dataset.config['pipeline'][config])
        elif config in dataset.config['network']:
            return NetworkPipeline(dataset, name, dataset.config['network'][config])
        else:
            try:
                return FunctionPipeline(dataset, name, config)
            except ValueError:
                raise ValueError("Wrong value for pipeline {}: {}".format(name, config))
    elif isinstance(config, dict):
        if 'criterion' in config:
            return BranchPipeline(dataset, name, config)
        else:
            return LogogramPipeline(dataset, name, config)
    else:
        raise ValueError("Wrong value for pipeline {}: {}".format(name, config))


class Pipeline:
    ''' A pipeline combines networks and logical steps into a computational
    graph that can be used for the task of detection or classification of
    logograms or graphemes.'''

    def __init__(self, dataset, name):
        '''This method shouldn't be called directly, please use the dataset
        method [get_pipeline](quevedodatasetdatasetget_pipeline).'''
        # Dataset: Parent dataset
        self.dataset = dataset
        # str: Name of the pipeline
        self.name = name

    def run(a: Annotation):
        '''Run the pipeline on the given annotation.

        Args:
            a (Annotation): Annotation to run the pipeline on.
        '''
        raise NotImplementedError


class SequencePipeline(Pipeline):
    '''A pipeline that runs a sequence of other pipelines.'''

    def __init__(self, dataset, name, config):
        super().__init__(dataset, name, config)
        self.steps = [create_pipeline(dataset, f'{name}.{str(i)}', step)
                      for i, step in enumerate(config)]

    def run(self, a: Annotation):
        for p in self.steps:
            a = p.run(a)


class NetworkPipeline(Pipeline):
    '''A pipeline step that runs a network on the given annotation.'''

    def __init__(self, dataset, name, config):
        super().__init__(dataset, name)
        self.network = dataset.get_network(config)

    def run(self, a: Annotation):
        self.network.auto_annotate(a)


class LogogramPipeline(Pipeline):
    '''A pipeline for detecting graphemes within a logogram and then classifying
    them, using networks or sub pipelines.'''

    def __init__(self, dataset, name, config):
        super().__init__(dataset, name)
        self.detect = create_pipeline(dataset, f'{name}.detect', config['detect'])
        self.classify = create_pipeline(dataset, f'{name}.classify', config['classify'])

    def run(self, a: Annotation):
        self.detect.run(a)
        for g in a.graphemes:
            self.classify.run(g)


class BranchPipeline(Pipeline):
    '''A pipeline that runs one of many possible branches depending on a
    criterion. The criterion can be:

    - a tag name: the pipeline will run the branch corresponding to the tag
      value (only for graphemes)
    - a meta tag: the pipeline will run the branch corresponding to the meta
      tag value (graphemes and logograms)
    - a lambda expression: the pipeline will run the branch corresponding to
      the result of the lambda expression, which will receive the annotation as
      parameter.
    '''

    def __init__(self, dataset, name, config):
        super().__init__(dataset, name)
        crit = config['criterion']
        self.criterion = crit
        if crit.startswith('lambda'):
            self.get_branch = eval(self.criterion)
        elif crit in dataset.config['tag_schema']:
            self.get_branch = lambda a, crit=crit: a.tags.get(crit)
        elif crit in dataset.config['meta_schema']:
            self.get_branch = lambda a, crit=crit: a.meta.get(crit)
        else:
            raise ValueError("Wrong criterion for {}: {}".format(name, config))

        self.branches = {
            branch: create_pipeline(dataset, f'{name}.{branch}', config=branch)
            for branch in config['branches']
        }

    def run(self, a: Annotation):
        branch = self.get_branch(a)
        if branch is None and '*' in self.branches:
            branch = '*'
        if branch is not None:
            self.branches[branch].run(a)


class FunctionPipeline(Pipeline):
    '''A pipeline that runs a user-defined function. The config should be
    a string in the form 'module.py:function'. 'module.py' should be a file
    in the `scripts` directory of the dataset, and 'function' should be the
    name of a function in that file, that accepts a dataset and annotation
    and returns nothing.'''

    def __init__(self, dataset, name, config):
        super().__init__(dataset, name)
        module, function = config.split(':')
        module = module_from_file(module, dataset.script_path)
        self.function = getattr(module, function)

    def run(self, a: Annotation):
        self.function(self.dataset, a)
