![Quevedo Logo](quevedo/logo.png)

# Quevedo

Quevedo is a python tool for managing datasets of images with compositional
semantics, with a focus on the training and evaluation of machine learning
algorithms on these images.

Quevedo is part of the [VisSE project](https://www.ucm.es/visse). The code can
be found at [GitHub](https://github.com/agarsev/quevedo), and detailed
documentation HERE (TODO).

## Features

- Dataset management, including hierarchical dataset organization, subset
    partitioning, and semantically guided data augmentation.
- Structural annotation of source images using a web interface, with support for
    different users and the live visualization of data processing scripts.
- Deep learning network management, training, configuration and evaluation,
    using [darknet].

## Installation

Quevedo requires `python >= 3.7`, and can be installed from PyPI: (TODO)

```shell
$ python3 -m pip install quevedo
```

Or directly from the wheel in the release file (TODO)

```shell
$ curl blabla
$ python3 -m pip install quevedo-wheel-blabla
```

To use the neural network module, you will also need [to install darknet](TODO:
link to docs nets#installation).

### Development

To develop on quevedo, we use [poetry] as our environment, dependency and build
management tool. In the quevedo code directory, run:

```shell
$ poetry install
```

Then you can run quevedo with

```shell
$ poetry run quevedo
```

## Usage

To create a dataset:

```shell
$ quevedo -D path/to/new/dataset create
```

Then you can **cd** into the dataset directory so that the `-D` option is not
needed.

To see information about a downloaded dataset:

```shell
$ quevedo info
```

To launch the web interface

```shell
$ quevedo web
```

For more information, and the list of commands, run `quevedo --help` or `quevedo
<command> --help` or see [here](TODO: link to docs/cli.md).

## Dependencies

Quevedo makes use of the following open source projects:

- [python 3]
- [poetry]
- [darknet]
- [click]
- [flask]
- [preactjs]

Additionally, we use the [toml] and [forcelayout] libraries, and build our
documentation with [mkdocs].

## About

Quevedo is licensed under the [Open Software License version
3.0](https://opensource.org/licenses/OSL-3.0).

### VisSE team

- [Antonio F. G. Sevilla](https://github.com/agarsev) <afgs@ucm.es>
- [Alberto Díaz Esteban](https://www.ucm.es/directorio?id=20069)
- [Jose María Lahoz-Bengoechea](https://ucm.es/lengespyteoliter/cv-lahoz-bengoechea-jose-maria)

[darknet]: https://pjreddie.com/darknet/install/
[poetry]: https://python-poetry.org/
[python 3]: https://www.python.org/
[click]: https://click.palletsprojects.com/
[flask]: https://flask.palletsprojects.com/en/2.0.x/
[preactjs]: https://preactjs.com/
[toml]: https://pypi.org/project/toml/
[forcelayout]: https://pypi.org/project/forcelayout/
[mkdocs]: https://www.mkdocs.org/
