![Quevedo Logo](quevedo/logo.png)

# Quevedo

Quevedo is a tool for managing datasets of images with complex semantics, with
a focus on the training and evaluation of machine learning algorithms on these
images.

Quevedo is part of the [VisSE project][VISSE].

## Features

- SW dataset management (annotation, extraction, preparation)
- Deep learning network training and testing

## Usage

Base requirements: [python 3], [poetry], [darknet].

- [ ] Install darknet for training
- [ ] Install with wheel
- [ ] Install for development - poetry, dependencies, building, etc

## Getting started

- Development: `poetry run quevedo -D <PATH_TO_THE_DATASET> command`.
- In the dataset directory: `quevedo command`.
- In other directory: `quevedo -D <PATH_TO_THE_DATASET> command`.

For more information, and the list of commands, run `poetry run quevedo --help`.

## About the dataset

Datasets are plain directories with a specified structure inside:

- `config.toml`: information and configuration for the dataset.
- `real`: directory with "real" SW transcriptions (from humans), organized in
  subdirectories. Transcriptions are numbered starting from `1`. For each
  transcription, there must be an image file (`{number}.png`). There can be also
  annotation files (`{number}.json`) and darknet-format bounding boxes files
  (`{number}.txt`).
- `symbols`: directory with the symbols extracted from the real transcriptions.
- `generated`: directory with generated images that look like SW trascriptions
  and can be used to augment the training data.
- `experiments`: directory with configuration for different train/test
  experiments.

## Author

Antonio F. G. Sevilla <afgs@ucm.es>


[darknet]: https://pjreddie.com/darknet/install/
[poetry]: https://python-poetry.org/
[python 3]: https://www.python.org/
[VISSE]: https://www.ucm.es/visse
