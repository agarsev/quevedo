# Pipelines

!!! note "New in v1.2"
    Pipelines are new in version 1.2.

Quevedo allows you to train different [neural networks](nets.md) to recognize
different objects and features. These networks can then be composed into
a pipeline to build an expert system, capable of performing a bigger task than
each of the networks by themselves.

For example, a detection network can first locate the graphemes within
a logogram, and then specialist networks used to classify each of the graphemes.

When using quevedo in the command line, you can choose the pipeline to test or
execute with the `-P` flag (equivalent to the `-N` flag for networks). In the
web interface, the pipelines are available along the trained networks and user
functions for the user to run and visualize.

!!! note
    Quevedo pipelines can be used to create expert systems for processing
    visually complex images. One such example, for the case of SignWriting, is
    described in the article [Automatic SignWriting Recognition](https://eprints.ucm.es/id/eprint/69235/).

## Pipeline configuration

Pipelines are added to the `config.toml` file of the dataset. Each entry is the
name of the pipeline, added to the "pipeline" table. There are a number of types
of pipelines that can be used, each with their own configuration, but there are
some common options.

### Common options

Options for the pipelines often take as value the name of a neural network. Most
of the time, instead of a neural network, the name of a pipeline can be used.
Quevedo will search the configuration file for pipelines or networks with
a matching name, so neither "network" nor "pipeline" need to be prepended.

If a "subsets" key is given to a pipeline, you will be able to use the
[`test`](cli.md#test) command to evaluate the performance of the pipeline on
those sets. Testing pipelines follows the same rules as for networks, and uses
the configured test folds. Training full pipelines is not yet supported, please
train the networks individually.

Pipelines can also use the `extend` keyword to inherit configuration from
another pipeline, making it easy to set the same subsets to test all pipelines,
or share some of the options.

## Logogram recognizer

A logogram recognizer pipeline has two steps. The first step uses a [detector
network](nets.md#detector) to find graphemes in an image. An optional second
step uses a [classifier network](nets.md#classifier) or another pipeline to then
extract the tags for each of the graphemes. The end result is the detected
logogram but with the graphemes augmented by the classifier.

```toml
# Example logogram pipeline. It uses a network named "detector" to find the
# graphemes, and then further classifies them with a network named "classifier"
[pipeline.logograms]
detect = "detector"
classify = "classifier"
```

## Sequence classifier

A sequence classifier uses many classifier networks or pipelines to iteratively
augment the annotation of a grapheme. It has one single option, `sequence`,
which is a list of the sub-systems to run.

Additionally to networks and pipelines, the steps in the sequence can be lambda
functions to run on the grapheme, or longer functions defined in a user script.
For this, place the script in the `scripts` directory, and use as step
`script_name.py:function_name`.

```toml
# Example sequence pipeline. It uses a network called "classifier1" to find
# a first possible set of tags for the grapheme. Then, a function
# "error_correction" in the "functions.py" user script fixes some common errors.
# A second network called "classifier2" makes use of the fixed grapheme to get
# a better prediction.
[pipeline.sequence]
extend = "defaults"
sequence = [
    "classifier1"
    "funtions.py:error_correction",
    "classifier2"
]
```

## Branching classifier

A branching pipeline can serve to classify graphemes using different networks or
pipelines according to some of the grapheme characteristics. A `criterion`
option sets the value to use to choose the branch, and then the other options
are the networks or sub-pipelines for each branch. The criterion can be the name
of a tag, or a lambda function to call on the grapheme.

```toml
# Example branching pipeline
[pipeline.branching]
criterion = "lambda g: g.tags.get('TAG1')"
criterion = "TAG1" # equivalent to the previous one
value1 = "classifier_for_value1s"
value2 = "classifier_for_value2s"
```
