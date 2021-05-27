# Use as a library

Quevedo can be used as a command line application to manage a dataset, but it
can also be used from other Python code to make programatic access to the
dataset more convenient. The documentation for the main objects that might be
useful is included below.

## Example

```
from quevedo import Dataset, Target

ds = Dataset('path/to/the/dataset')

ds.get_single(Target.GRAPH, 'subset', 32)
```

## Reference

### Dataset

![mkapi](quevedo.Dataset)

### Target

Quevedo annotations are of two types, logograms and graphemes, both derived from
the parent class `Annotation`. When it is necessary to distinguish logograms and
graphemes in a process, there is the enum `Target`, which can take the values
`Target.GRAPH` or `Target.LOGO`. the values `Target.GRAPH` or `Target.LOGO`.

### Annotation

![mkapi](quevedo.annotation.Annotation)
![mkapi](quevedo.annotation.Logogram)
![mkapi](quevedo.annotation.Grapheme)

### Network

![mkapi](quevedo.network.network.Network)
