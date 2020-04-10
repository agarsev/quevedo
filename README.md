# SWREC

SignWriting RECognition tool.

## Features

- SW dataset management (annotation, extraction, preparation)
- Deep learning network training and testing

## Usage

Base requirements: [python 3], [poetry], [darknet].

Install: `poetry install`.

Usage: `poetry run swrec <PATH_TO_THE_DATASET> command`.

For more information, and the list of commands, run `poetry run swrec --help`.

## About the dataset

Datasets are plain directories with a specified structure inside:

- `info.yaml`: information and configuration for the dataset.
- `real`: directory with "real" SW transcriptions (from humans). Transcriptions
  are numbered starting from `1`. For each transcription, there must be an image
  file (`{number}.png`). There can be also annotation files (`{number}.json`)
  and darknet-format bounding boxes files (`{number}.txt`).
- `symbols`: directory with the symbols extracted from the real transcriptions.
- `generated`: directory with generated images that look like SW trascriptions
  and can be used to augment the training data.

## Author

Antonio F. G. Sevilla <afgs@ucm.es>


[darknet]: https://pjreddie.com/darknet/install/
[poetry]: https://python-poetry.org/
[python 3]: https://www.python.org/
