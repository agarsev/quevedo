# User Guide

This guide will walk through the steps necessary to create and populate a
Quevedo dataset, and some examples on its use.

## Install

Quevedo is a python package, but it depends on darknet too, which is a C library
by the inventor of the YOLO algorithm.

To install Quevedo, you can use pip with the wheel released here (TODO):

    $ python3 -m pip install quevedo-*.whl[web,force_layout]

This will install all extras too (web interface, force_layout for data
augmentation). If you don't need them you can leave them out.

If Quevedo was properly installed, the `quevedo` binary should be available in
the path. You can test it using:

    $ quevedo --help

Which will print useful help about the tool.

## Repository Creation

A Quevedo repository is a collection of data (in image form) and metadata
describing that image, with the purpose of training an automatic system to
detect within new images the metadata contained within.

It has been developed in the context of SignWriting recognition.

To create a new repository, first create the directory where the data will be
stored, then call `quevedo create` in that directory. You will be asked for the
basic dataset information, and then the directory will be populated with the
basic structure necessary for quevedo to operate.

    $ mkdir signwriting
    $ cd signwriting
    $ quevedo create
    Title of the dataset: SignWriting
    Description of the dataset: VISSE SignWriting dataset
    Created dataset 'SignWriting' at '/home/agarsev/visse/signwriting'

    Configuration can be found in 'config.toml'. We recommend
    reading it now and adapting it to this dataset, but you can
    always do it later or use the command `config`.
    View config file now? [Y/n]:

The different directories and files inside a Quevedo repository use standard
formats, so can be inspected manually and perused with other typical
command-line tools. However, you don't need to do it, and can see the dataset as
a black box and only access it with the `quevedo` binary.

A special file inside the dataset is found at the root, called `config.toml`. This
file, in TOML format, contains all the user configuration of the dataset. You
can view and edit it manually, or running `quevedo config`.

You can see a summary of the dataset information using the `info` command:

    $ quevedo info
    SignWriting
    ▔▔▔▔▔▔▔▔▔▔▔

    VISSE SignWriting dataset

    Tag schema: tag

    Real transcriptions: 0
    Annotated: 0/0
    Symbols extracted: no
    Transcriptions generated: no
    Darknet is not properly configured in config.toml

    Experiment: 'default'
    ▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔
    focus on symbol type learning and recognition

    Dataset is not ready for training
    Neural network hasn't been trained

::: Note
There are two ways to tell the `quevedo` binary what dataset to use. The first
and easiest, which will be used in this guide, is to `cd` to the dataset
directory. By default, `quevedo` assumes the current directory is the dataset to
manage.

Otherwise, most notably for scripting purposes, you can use the `-D` option to
quevedo, to give the path to the dataset. This must be used *before* any
commands, for example `quevedo -D /home/agarsev/visse/signwriting info`.

Creating the dataset this way will automatically create its directory, so it can
be a quick way to initialize it. It can also use relative paths:

    quevedo -D signwriting create

will create a subdirectory `signwriting` in the current directory, and
initialize it as a Quevedo dataset.
:::

## Adding images

Now that we have the structure for the dataset, it's time to populate it with
real data, i.e. images of writing transcriptions. These should be in some
directory in the filesystem, and must have `.png` extension. Then, just run
`quevedo add_images -i <PATH>`.

Example:

    $ quevedo add_images -i /home/agarsev/b22_vocab/
    Importing images from '/home/agarsev/b22_vocab/' to '/home/agarsev/visse/signwriting/real/default'...imported 136

Quevedo reports how many images were succesfully imported, and the path where
they were stored. As you can see, it put the images in a subdirectory of the
dataset named `real/default`. All "real" images (coming from informants, or
other type of *actual* observations) are stored in the `real` subdirectory. This
directory is itself split in subdirectories that can be used to organize
transcriptions in sets or batches. By default, images are assigned to the
`default` directory. To change this, you can use the `--name` option, like so:

    quevedo add_images -i <PATH> --name <NAME_OF_THE_SUBSET>

If you change your mind at any point, you can rename the subdirectories under
`real`, quevedo doesn't give any special meaning to subset names.

If you list the contents of the `real/default` directory, you will notice two
things:

1. *Filenames now are numbers*. Quevedo numbers transcriptions in a subset
   sequentially, so the pair subset name + number constitutes a unique id for
   each observation.
2. *JSON files*. Along with the transcriptions, there are some new `.json`
   files, also sequentially numbered. Quevedo stores metadata and annotations
   for the transcriptions in these files, which can be examined by hand or other
   tools. Each `<number>.json` file stores the metadata for the equally numbered
   `<number>.png` transcription.

The original file names for the transcriptions are kept in the annotation file,
in a "notes" field, in case it is useful information. The "notes" field is only
for users, quevedo does not peruse it in any way.

If some information is to be added to the whole subset, a markdown file can be
created in the subset directory with the name `README.md`. This file will be
displayed in the web interface, and humans navigating the dataset manually will 
immediately know to read it. This file can contain information regarding the
source of the data, annotator identities, etc. Quevedo doesn't use this file in
any way.

::: Note

Since the dataset is just a particular directory structure, with standard files
in appropriate locations, it is easy to version control it using a VCS like
git. Using `README.md` files in the appropriate locations helps users navigate
the dataset, and tracking their changes in a VCS allows date and authorship
information to be stored in a standard way.

Using a VCS also means keeping a history of the project, and being able to
revert changes if something goes wrong.

The root of the dataset is also a good place to store licensing information (in
a `LICENSE` file) and general human-readable information (in a `README.md`),
different from the configuration in `config.toml`.

Distributed VC systems like git also make it easy to share datasets, and
collaborate in their preparation and annotation. For example, the dataset we are
building in this guide can be accessed and examined at the URL @TODO@.

:::
