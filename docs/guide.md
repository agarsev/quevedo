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

- TODO: install darknet

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
