# Reference

## Datasets

Dataset objects are the main entry point for user code in Quevedo. They provide
methods to manage the dataset, but also to retrieve other objects within it.
Therefore, you don't usually need to create instances of other objects directly,
but rather use the methods in the Dataset class to get them already built.

For example:

```
from quevedo import Dataset, Target

ds = Dataset('path/to/the/dataset')

# annotation is of type quevedo.Grapheme, a subclass of quevedo.Annotation
annotation = ds.get_single(Target.GRAPH, 'subset', 32)
print(annotation.to_dict())

# net is of type quevedo.Network
net = ds.get_network('grapheme_classify')
net.auto_annotate(annotation)
annotation.save()

# creating a quevedo.Logogram (subclass of quevedo.Annotation)
new_a = ds.new_single(Target.LOGO, 'my_new_subset',
                      image_path='path/to/the/image',
                      graphemes=[
                          {'tags': ['character', 'letter_a'],
                           'box': [0.2, 0.6, 0.3, 0.3]},
                          {'tags': ['character', 'accute_accent']
                           'box': [0.2, 0.2, 0.1, 0.2]}
                      ])
```

### ![mkapi](quevedo.Dataset|short)

## Annotations

Quevedo annotations are of two types, logograms and graphemes, both derived from
the parent class `Annotation`. When it is necessary to distinguish logograms and
graphemes in a process, there is the enum `Target`, which can take the values
`Target.GRAPH` or `Target.LOGO`. the values `Target.GRAPH` or `Target.LOGO`.

There is also the `BoundGrapheme` class, used to represent each of the graphemes
which make up a logogram.

### ![mkapi](quevedo.annotation.Annotation|short)
### ![mkapi](quevedo.annotation.Grapheme|short)
### ![mkapi](quevedo.annotation.Logogram|short)
### ![mkapi](quevedo.annotation.logogram.BoundGrapheme|short)
### ![mkapi](quevedo.annotation.logogram.Edge|short)

## Networks

Network objects in Quevedo represent the network itself, but also their
configuration, training and testing process, and use. There are two types of
networks, [Detector](nets.md#detector) networks and
[Classifier](nets.md#classifier) networks, which work on logograms and graphemes
respectively.

The Network base class documented here is a base class that defines general
behaviour, but code specific to each type of network lives in its own class.
Therefore, you should get the network from a Quevedo dataset's method
[`get_network`](#quevedodatasetdatasetget_network) so that the proper instance
is built.

### ![mkapi](quevedo.network.network.Network|short)

## Pipelines

[Pipeline](pipes.md) objects in Quevedo can often act as substitutes for
networks, to perform their task but using a more complex system of networks and
steps. There are a number of types of pipelines, each represented by a different
class in the code, and a base class that serves as common interface. To get
a configured pipeline from a dataset, use its
[`get_pipeline`](#quevedodatasetdatasetget_pipeline) method.

### ![mkapi](quevedo.pipeline.Pipeline|short)
### ![mkapi](quevedo.pipeline.NetworkPipeline|short)
### ![mkapi](quevedo.pipeline.LogogramPipeline|short)
### ![mkapi](quevedo.pipeline.SequencePipeline|short)
### ![mkapi](quevedo.pipeline.BranchPipeline|short)
### ![mkapi](quevedo.pipeline.FunctionPipeline|short)
