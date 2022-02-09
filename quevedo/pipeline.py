# 2021-11-10 Antonio F. G. Sevilla <afgs@ucm.es>
# Licensed under the Open Software License version 3.0

from inspect import signature

from quevedo.annotation import Annotation, Logogram, Grapheme
from quevedo.run_script import module_from_file


def create_pipeline(dataset, name=None, config=None):
    '''Factory function to create a pipeline.'''
    if config is None and name is None:
        raise ValueError("Either a pipeline configuration or a name is needed to create a pipeline")

    if config is None:
        config = dataset.get_config('pipeline', name)

    if name is None:
        name = 'anonymous'

    if isinstance(config, list):
        return SequencePipeline(dataset, name, config)
    elif isinstance(config, str):
        if config in dataset.config['pipeline']:
            return create_pipeline(dataset, name, dataset.config['pipeline'][config])
        elif config in dataset.config['network']:
            return NetworkPipeline(dataset, name, config)
        else:
            try:
                return FunctionPipeline(dataset, name, config)
            except ValueError:
                raise ValueError("Wrong value for pipeline {}: {}".format(name, config)) from None
    elif isinstance(config, dict):
        if 'criterion' in config:
            return BranchPipeline(dataset, name, config)
        elif 'sequence' in config:
            return SequencePipeline(dataset, name, config)
        else:
            return LogogramPipeline(dataset, name, config)
    else:
        raise ValueError("Wrong value for pipeline {}: {}".format(name, config))


class Pipeline:
    ''' A pipeline combines networks and logical steps into a computational
    graph that can be used for the task of detection or classification of
    logograms or graphemes.'''

    def __init__(self, dataset, name, config):
        '''This method shouldn't be called directly, please use the dataset
        method [get_pipeline](quevedodatasetdatasetget_pipeline).'''
        # Dataset: Parent dataset
        self.dataset = dataset
        # str: Name of the pipeline
        self.name = name
        # Configuration of the pipeline
        self.config = config
        # Target: whether input  is a logogram or a grapheme. Should be set by child classes.
        self.target = None

    def run(a: Annotation):
        '''Run the pipeline on the given annotation.

        Args:
            a (Annotation): Annotation to run the pipeline on.
        '''
        raise NotImplementedError

    def predict(self, image_path):
        '''Run the pipeline on the given image and return the resulting
        annotation.

        Args:
            image_path (str): Path to the image to run the pipeline on.

        Returns:
            Annotation: The resulting annotation.
        '''
        if Logogram.target in self.target:
            a = Logogram(image_path)
        else:
            a = Grapheme(image_path)
        self.run(a)
        return a


class SequencePipeline(Pipeline):
    '''A pipeline that runs a sequence of other pipelines. All steps should have
    the same target.'''

    def __init__(self, dataset, name, config):
        super().__init__(dataset, name, config)
        if isinstance(config, dict):
            config = config['sequence']
        self.steps = [create_pipeline(dataset, f'{name}.{str(i)}', step)
                      for i, step in enumerate(config)]
        self.target = self.steps[0].target

    def run(self, a: Annotation):
        for p in self.steps:
            p.run(a)


class NetworkPipeline(Pipeline):
    '''A pipeline step that runs a network on the given annotation.'''

    def __init__(self, dataset, name, config):
        super().__init__(dataset, name, config)
        self.network = dataset.get_network(config)
        self.target = self.network.target

    def run(self, a: Annotation):
        self.network.auto_annotate(a)


class LogogramPipeline(Pipeline):
    '''A pipeline for detecting graphemes within a logogram and then classifying
    them, using networks or sub pipelines.'''

    def __init__(self, dataset, name, config):
        super().__init__(dataset, name, config)
        if 'detect' in config:
            self.detect = create_pipeline(dataset, f'{name}.detect', config['detect'])
        else:
            self.detect = None

        if 'classify' in config:
            self.classify = create_pipeline(dataset, f'{name}.classify', config['classify'])
        else:
            self.classify = None

        self.target = Logogram.target

    def run(self, a: Annotation):
        if self.detect is not None:
            self.detect.run(a)
        if self.classify is not None:
            for g in a.graphemes:
                self.classify.run(g)


class BranchPipeline(Pipeline):
    '''A pipeline that runs one of many possible branches depending on a
    criterion. The criterion can be:

    - a tag name: the pipeline will run the branch corresponding to the tag
      value. Can also be a meta tag.
    - a lambda expression: the pipeline will run the branch corresponding to
      the result of the lambda expression, which will receive the annotation as
      parameter.

    All branches should have the same target.
    '''

    def __init__(self, dataset, name, config):
        super().__init__(dataset, name, config)
        crit = config['criterion']
        self.criterion = crit
        if crit.startswith('lambda'):
            self.get_branch = eval(self.criterion)
        elif crit in dataset.config['g_tags']:
            self.get_branch = lambda a, crit=crit: a.tags.get(crit)
        elif crit in dataset.config['l_tags']:
            self.get_branch = lambda a, crit=crit: a.tags.get(crit)
        elif crit in dataset.config['meta_tags']:
            self.get_branch = lambda a, crit=crit: a.meta.get(crit)
        else:
            raise ValueError("Wrong criterion for {}: {}".format(name, config))

        self.branches = {
            key: create_pipeline(dataset, f'{name}.{key}', config=config[key])
            for key in config if key != 'criterion'
        }

        self.target = self.branches[list(self.branches.keys())[0]].target

    def run(self, a: Annotation):
        branch = self.get_branch(a)
        if branch is None and '*' in self.branches:
            branch = '*'
        if branch is not None:
            self.branches[branch].run(a)


class FunctionPipeline(Pipeline):
    '''A pipeline that runs a user-defined function.

    The config should be a string in the form 'module.py:function'. 'module.py'
    should be a file in the `scripts` directory of the dataset, and 'function'
    should be the name of a function in that file, that accepts an annotation
    and a dataset and returns nothing. Alternatively, a string containing
    a lambda function, receiving the same arguments, can be used.

    The target of this pipeline is deduced from the signature of the function.
    This is often inconsequential, but if this network is the first of
    a sequence or branching, its target will be the target for the whole
    pipeline. To ensure correct deduction, use a type annotation of Logogram or
    Grapheme for the second parameter.'''

    def __init__(self, dataset, name, config):
        super().__init__(dataset, name, config)

        if config.startswith('lambda'):
            self.function = eval(config)
        else:
            module, function = config.split(':')
            module = module_from_file(module, dataset.script_path)
            self.function = getattr(module, function)

        a, _ = signature(self.function).parameters.values()
        try:
            self.target = a.annotation.target
        except AttributeError:
            self.target = Logogram.target if a.name.startswith('l') else Grapheme.target

    def run(self, a: Annotation):
        self.function(a, self.dataset)
