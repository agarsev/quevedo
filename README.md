![Quevedo Logo](quevedo/logo.png)

# Quevedo

Quevedo is a python tool for creating, annotating and managing datasets of
graphical languages, with a focus on the training and evaluation of machine
learning algorithms for their recognition.

Quevedo is part of the [VisSE project](https://www.ucm.es/visse). The code can
be found at [GitHub](https://github.com/agarsev/quevedo), and [detailed
documentation here](https://agarsev.github.io/quevedo).

## Features

- Dataset management, including hierarchical dataset organization, subset
    partitioning, and semantically guided data augmentation.
- Structural annotation of source images using a web interface, with support for
    different users and the live visualization of data processing scripts.
- Deep learning network management, training, configuration and evaluation,
    using [darknet].

## Installation

Quevedo requires `python >= 3.7`, and can be installed from
[PyPI](https://pypi.org/project/quevedo/):

```shell
$ pip install quevedo
```

Or, if you want any extras, like the web interface:

```shell
$ pip install quevedo[web]
```

Or directly from the wheel in the [release
file](https://github.com/agarsev/quevedo/releases):

```shell
$ pip install quevedo-{version}-py3-none-any.whl[web]
```

You can test that quevedo is working

To use the neural network module, you will also need [to install
darknet](https://agarsev.github.io/quevedo/latest/nets/#installation).

## Usage

To create a dataset:

```shell
$ quevedo -D path/to/new/dataset create
```

Then you can **cd** into the dataset directory so that the `-D` option is not
needed.

You can also download an example dataset from this repository (`examples/toy_arithmetic`).

To see information about a dataset:

```shell
$ quevedo info
```

To launch the web interface (you must have installed the "web" extra):

```shell
$ quevedo web
```

For more information, and the list of commands, run `quevedo --help` or `quevedo
<command> --help` or see [here](https://agarsev.github.io/quevedo/latest/cli/).

## Development

To develop on quevedo, we use [poetry] as our environment, dependency and build
management tool. In the quevedo code directory, run:

```shell
$ poetry install
```

Then you can run quevedo with

```shell
$ poetry run quevedo
```

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

The web interface includes a copy of [preactjs] for ease of offline use, distributed
under the [MIT License](https://github.com/preactjs/preact/blob/master/LICENSE).

Quevedo is part of the project ["Visualizando la SignoEscritura" (Proyecto VisSE,
Facultad de Informática, Universidad Complutense de
Madrid)](https://www.ucm.es/visse) as part of the
program for funding of research projects on Accesible Technologies financed by
INDRA and Fundación Universia. An expert system developed using Quevedo is
described [in this article](https://eprints.ucm.es/id/eprint/69235/).

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
