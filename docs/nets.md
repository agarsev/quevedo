# Neural networks

One of the difficulties of processing visual languages automatically is input,
when it is presented in the form of images. Images are represented digitally as
collections of pixels, arrayed in memory in a way that makes sense for display
and storage, but which is completely disconnected to the meaning these images
have to humans. Additionally, if input is hand written, graphemes can present
variations which don't affect human understanding but which mean completely
different pixel patterns are present. And positioning of objects is again not
based on hard rules, but rather on visual interpretation.

For these reasons, machine learning techniques developed in the field of
computer vision are necessary to adequately process logograms and graphemes.
While the researcher can use any toolkit and algorithm they prefer, Quevedo
includes a module to facilitate using neural networks with Quevedo datasets.

## Darknet

[Darknet] is "an open source neural network framework written in C and CUDA",
developed by the inventor of the [YOLO] algorithm, Joseph Redmon. This framework
includes a binary and linked library which make configuring, training, and using
neural networks for computer vision straightforward and efficient.

The neural network module included with Quevedo needs darknet to be available.
This module automatically prepares network configuration and training files from
the metadata in the dataset, and can manage the training and prediction
process.

### Installation

We recommend using [this fork by Alexey
Bochkovskiy](https://github.com/AlexeyAB/darknet). Installation can vary
depending on your environment, including the CUDA and OpenCV (optional)
libraries installed, but with luck, the following will work:

```shell
$ git clone https://github.com/AlexeyAB/darknet
$ cd darknet
<edit the Makefile>
$ make
```

In the Makefile, you probably want to enable `GPU=1` and `CUDNN=1`, otherwise
training will be too slow. Depending on the GPU available and CUDA installation,
you might need to change the `ARCH` and `NVCC` variables. For Quevedo to use
Darknet, it is also necessary to set `LIBSO=1` so the linked library is built.
Finally, if you want to use Darknet's data augmentation, you probably want to
set `OPENCV=1` to make it faster.

After darknet is compiled, a binary (named `darknet`) and library
(`libdarknet.so` in linux) will be built. Quevedo needs to know where these
files are, so in the `[darknet]` section of the configuration, the path to the
binary and library must be set. By default, these point to a darknet
directory in the current directory. Some additional arguments to the darknet
binary for training can be set in the `options` key.

## Network configuration

Neural networks are ideal to deal with image data, due to their ability to
find patterns and their combinations. Quevedo can help with preparing the
configuration and training files to train darknet neural networks, can launch
the actual training, and can compute evaluation metrics on the resulting network
weights. It can also be used as a library to peruse the trained network in an
application, not only for research.

But no net is a silver bullet for every kind problem, and Quevedo datasets deal
with different types of data with complex annotations. Therefore, Quevedo allows
different network configurations to be kept in the configuration file, aiding
both ensemble applications and exploration of the problem space.

To add a neural network configuration to Quevedo, add a section to the
`config.toml` file with the heading `[network.<network_name>]`. The initial
configuration file that Quevedo creates for every dataset contains some examples
that can be commented out and modified.

Under this heading, different options can be set, like a `subject` key that
gives a brief description of the purpose of the network. The most important
configuration option is `task`, which can take the values `classify` or
`detect`.

### Classifier

Classifier networks can be used with individual graphemes, and therefore use the
data in the grapheme subsets of the dataset. Classify networks see the image as
a whole, and try to find the best matching "class" from the classes they have
been trained in. In Quevedo, classify networks are built with the
AlexNet[^AlexNet]
architecture , a CNN well suited to the task.

### Detector

Detector networks try to find objects in an image, and therefore are well suited
for finding the different graphemes that make up a logogram. Apart from
detecting the boundary boxes of the different objects, they can also do
classification of the objects themselves. Depending on the nature and complexity
of the data, classification of graphemes can be performed by the same network
that detects them within a logogram, or can be better split into a different (or
many) classifier networks. The detector network architecture used by Quevedo is
YOLOv3[^YOLOv3].

!!! note
    After the prepare step of network use, a network configuration file is
    produced that can be edited to fine-tune the network architecture.

### Tag selection

Since Quevedo datasets support a multi-tag annotation schema, a single
"class"/"label" has to be selected for the networks in order to perform
classification (including detector networks, since they have a classification
step). By default the first tag of the tag schema will be used, but other tags
can be selected by writing `tag = "some_tag_in_the_schema"`. A combination of
the tags can be used by listing them, for example
`tag = [ "some_tag", "some_other_tag" ]`. This will produce a single label for
each grapheme by combining the values of the tags with an underscore in between,
and train and evaluate the network with that single label.

### Annotation selection

To specify what subsets of data to use for training and testing of a neural
network, we can list the names in the `subsets` option.  Additionally, we might
want to select some logograms or graphemes to use for a particular network based
on the tag values. We can do this by leaving the relevant tags for that network
empty, in which case Quevedo will skip the annotation.

In classify networks, finer control can also be achieved using a "filter"
section for the network configuration. This filter accepts a key `criterion`
which determines what tag from the annotation schema to use to select
annotations. Then, an `include` or `exclude` key can be set to the list of
values to filter. When `include` is used, if a grapheme is tagged with any of
the values in the list, it is included for training and test, otherwise it is
ignored. With `exclude`, the reverse happens.

### Data augmentation

Recent versions of darknet include automatic data augmentation that happens "on
the fly", while the network is being trained. This data augmentation is not
based on semantics of the images, but on image properties like contrast or
rotation. By slightly and randomly modifying the images that the network is
trained on, overfitting can be avoided and better generalization achieved. Some
relevant options for grapheme and logogram recognition are supported by Quevedo,
and if set in the network configuration will be written into the Darknet
configuration file.

The header to use is `[network.<network_name>.augment]`, and
the options supported are `angle` (randomly rotate images up to this amount of
degrees), `exposure` (change brightness of the image), `flip` (if set to `1`,
images are sometimes flipped), and, only for classify networks `aspect`, which
modifies the grapheme width/height relation.

In visual writing systems, not all of this transformations are without meaning,
so by default they are disabled so that the user can choose which options make
sense for their particular use case and data.

## Usage

### At the command line
 
Once the network has been configured, the files necessary for training it can be
created by running [`prepare`](cli.md#prepare). This will create a directory in
the dataset, under `networks`, with the name of the neural network. By default,
Quevedo will use the neural network marked with `default = True`, so to change
to a different one use the option `-N <network>` (since this is an option common
too many commands, it must be used after the `quevedo` binary name but *before*
the command).

Once the directory with all the files needed for training has been created, a
simple invocation of [`train`](cli.md#train) will launch the darknet executable to
train the neural network. This command can be interrupted, and if enough time
has passed that some partial training weights have been found, it can be later
resumed by calling `train` again (to train from zero, use `--no-resume`).

The weights obtained by the training process will be stored in the network
directory with the name `darknet_final.weights`. This is a darknet file that can
be used independently of Quevedo.

To evaluate the results, the [`test`](cli.md#test) command can be used, which will
get the predictions from the net for the annotations marked as "test" (see
[`split`](cli.md#split)) and output some metrics, and optionally the full
predictions as a **csv** file so that fine metrics or visualizations can be
computed with something else (like [R]). The [`predict`](cli.md#predict) command
can be used to directly get the predictions from the neural network for some
image, not necessarily one in the dataset.

Since commands can be chained, a full pipeline of training and testing the net
can be written as:

```shell
$ quevedo -D path/to/dataset -N network_name prepare train test
```

### At the web interface

Trained neural networks can also be used at the web interface. Networks for
detection will be available for logograms, and classifier ones will be available
for graphemes. They will be listed at the top right of the interface. When
running them, the current annotation image will be fed to the neural network,
and the predictions applied (but not saved until the user presses the **save**
button). This can be used to visualize the neural network results, or to
bootstrap manual annotation of logograms and graphemes.

TODO: image

TODO: link to page about web

## Example Configuration

```toml
# Annotations for each grapheme
tag_schema = [ "COARSE", "FINE", "ALTERATION" ]

# Configuration for the darknet binary and library
[darknet]
path = "darknet/darknet" 
library = "darknet/libdarknet.so"
# By passing the -mjpeg_port argument to darknet, a live image of training
# progress can be seen at that port (in localhost)
options = [ "-mjpeg_port", "8090" ]

# Detect graphemes in logograms, and also assign a coarse-grained tag
[network.logograms]
subject = "Detect and classify coarse grain graphemes in a logogram"
default = true
task = "detect"
tag = "COARSE"
subsets = [ "italian", "spanish" ]

[network.shapes]
subject = "Classify grapheme shapes"
task = "classify"
tag = [ "FINE" ]
subsets = [ "simple", "complicated" ]

# When training grapheme classification, augment the data
[network.shapes.augment]
angle = 10
exposure = 0.5

# Some graphemes present alterations, annotated in the "ALTERATION" tag. We want
# to train a specific classifier for these graphemes
[network.altered]
subject = "Classify the alterations of 'complicated' graphemes"
task = "classify"
# The label to train will be a concatenation of the "fine" tag and the
# "alteration"
tag = [ "FINE", "ALTERATION" ]
# We have stored the graphemes with these alterations in the "complicated"
# subset
subsets = [ "complicated" ]

# Only graphemes with the values "multifaceted" or " accentuated" for the
# "FINE" tag will be used
[network.altered.filter]
criterion = "FINE"
include = [ "multifaceted", "accentuated" ]
```

[Darknet]: http://pjreddie.com/darknet/
[YOLO]: https://pjreddie.com/darknet/yolo/
[R]: https://www.r-project.org/

[^AlexNet]:
    Krizhevsky, Alex; Sutskever, Ilya; Hinton, Geoffrey E.
    (2017). ["ImageNet classification with deep convolutional neural
    networks"](https://papers.nips.cc/paper/4824-imagenet-classification-with-deep-convolutional-neural-networks.pdf).
    *Communications of the ACM. 60 (6): 84–90. doi:10.1145/3065386. ISSN 0001-0782.
    S2CID 195908774.*

[^YOLOv3]:
    Redmon, Joseph and Farhadi, Ali (2018). ["YOLOv3: An Incremental
    Improvement"](https://arxiv.org/pdf/1804.02767.pdf;). *arXiv preprint
    arXiv:1804.02767.*
