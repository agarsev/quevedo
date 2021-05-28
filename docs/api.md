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
annotation = ds.get_single(Target.GRAPH, 'subset', 32)
print(annotation.to_dict())

net = ds.get_network('grapheme_classify')
net.auto_annotate(annotation)
annotation.save()
```

### ![mkapi](quevedo.Dataset)

## Annotations

Quevedo annotations are of two types, logograms and graphemes, both derived from
the parent class `Annotation`. When it is necessary to distinguish logograms and
graphemes in a process, there is the enum `Target`, which can take the values
`Target.GRAPH` or `Target.LOGO`. the values `Target.GRAPH` or `Target.LOGO`.

There is also the `BoundGrapheme` class, used to represent each of the graphemes
which make up a logogram.

### ![mkapi](quevedo.annotation.Annotation)
### ![mkapi](quevedo.annotation.Grapheme)
### ![mkapi](quevedo.annotation.Logogram)
### ![mkapi](quevedo.annotation.logogram.BoundGrapheme)

## Networks

![mkapi](quevedo.network.network.Network)
