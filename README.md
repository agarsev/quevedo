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

Base requirements: [python 3], [poetry], [darknet].

- [ ] Install darknet for training
- [ ] Install with wheel
- [ ] Install for development - poetry, dependencies, building, etc

## Usage

- Development: `poetry run quevedo -D <PATH_TO_THE_DATASET> command`.
- In the dataset directory: `quevedo command`.
- In other directory: `quevedo -D <PATH_TO_THE_DATASET> command`.

For more information, and the list of commands, run `poetry run quevedo --help`.

## About

Author: [Antonio F. G. Sevilla](https://github.com/agarsev) <afgs@ucm.es>

Quevedo is licensed under the Open Software License version 3.0.

[darknet]: https://pjreddie.com/darknet/install/
[poetry]: https://python-poetry.org/
[python 3]: https://www.python.org/
