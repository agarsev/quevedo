# Command Line Interface

```txt
Usage: quevedo [OPTIONS] COMMAND1 [ARGS]... [COMMAND2 [ARGS]...]...

  Quevedo is a tool for managing datasets of images with compositional
  semantics.

  This includes file management, annotation of data, and neural network
  training and use.

  The -D and -N flags are global, and affect all commands used afterwards. For
  example, to run a full experiment for neural network 'one', run:

      quevedo -D path/to/dataset -N one split -p 80 prepare train test

Options:
  -D, --dataset PATH  Path to the dataset to use, by default use current
                      directory
  -N, --network TEXT  Neural network configuration to use
  --help              Show this message and exit.

Commands:
  add_images  Import images from external directories into the dataset.
  config      Edit dataset configuration.
  create      Create and initialize a Quevedo dataset.
  extract     Extract graphemes from annotated logograms.
  generate    Generate artificial logograms from existing graphemes.
  info        Get general status information about a dataset.
  predict     Get predictions for an image using the trained neural network.
  prepare     Create the files needed for training and using this network.
  run_script  Run a data processing script on dataset objects.
  split       Split files into train and test groups.
  test        Compute evaluation metrics for a trained neural network.
  train       Train the neural network.
  web         Run a web interface to the dataset.
```

## `split`

```txt
Usage: quevedo split [OPTIONS]

  Split files into train and test groups.

  The annotations in the given subsets will be split into two groups, one for
  training and one for test.  This split will not be done physically but
  rather as a mark stored on the annotation file.

  If no subsets are given, all annotations will be marked. If homogeneous
  split is required, call this command once for each set.

Options:
  -g, --grapheme-set TEXT         Grapheme set(s) to split.
  -l, --logogram-set TEXT         Logogram set(s) to split.
  -p, --percentage INTEGER RANGE  [0<=x<=100]
  --seed INTEGER                  A seed for the random split algorithm.
  --help                          Show this message and exit.
```

## `config`

```txt
Usage: quevedo config [OPTIONS]

  Edit dataset configuration.

  This command is a simple convenience to launch an editor open at the
  configuration file (config.toml).

Options:
  -e, --editor TEXT  Editor to use instead of the automatically detected one
  --help             Show this message and exit.
```

## `info`

```txt
Usage: quevedo info [OPTIONS]

  Get general status information about a dataset.

Options:
  --help  Show this message and exit.
```

## `create`

```txt
Usage: quevedo create [OPTIONS]

  Create and initialize a Quevedo dataset.

Options:
  --help  Show this message and exit.
```

## `add_images`

```txt
Usage: quevedo add_images [OPTIONS]

  Import images from external directories into the dataset.

  For now, images need to be in the PNG format, and have 3 channels (color)
  and 8 bit depth.

Options:
  -i, --image_dir PATH     Directory from which to import images.  [required]
  -g, --grapheme-set TEXT  Import the images to this grapheme set.
  -l, --logogram-set TEXT  Import the images to this logogram set.
  -m, --merge              Merge new images with existing ones, if any.
  -r, --replace            Replace old images with new ones, if any.
  --sort-numeric           Sort images ids by filename (numeric).
  --sort-alphabetic        Sort images ids by filename (alphabetic).
  --no-sort                Don't sort images to import.  [default]
  --help                   Show this message and exit.
```

## `extract`

```txt
Usage: quevedo extract [OPTIONS]

  Extract graphemes from annotated logograms.

  This command takes all the logograms in the given subset, extracts the
  graphemes annotated in each of them, and stores them as independent
  annotations (carrying over the relevant information) in the chosen grapheme
  subset.

Options:
  -f, --from TEXT  Logogram subset from which to extract graphemes.
  -t, --to TEXT    Grapheme subset where to place extracted graphemes.
  -m, --merge      Merge new graphemes with existing ones, if any.
  -r, --replace    Replace old graphemes with new ones, if any.
  --help           Show this message and exit.
```

## `generate`

```txt
Usage: quevedo generate [OPTIONS]

  Generate artificial logograms from existing graphemes.

  This command creates new logograms in the chosen subset by randomly
  combining graphemes together. The generation process can be somewhat
  controlled in the configuration file.

  Since the goal of this process is to perform data augmentation for training,
  only graphemes in the "train" group will be used.

Options:
  -f, --from TEXT  Grapheme subset to use
  -t, --to TEXT    Logogram subset where to place generated logograms.
  -m, --merge      Merge new logograms with existing ones, if any.
  -r, --replace    Replace old logograms with new ones, if any.
  --help           Show this message and exit.
```

## `prepare`

```txt
Usage: quevedo prepare [OPTIONS]

  Create the files needed for training and using this network.

  The training files, net configuration, and mapping from dataset tags to net
  classes are stored in a directory named after the chosen net (-N flag) under
  the `networks` path.

Options:
  --help  Show this message and exit.
```

## `train`

```txt
Usage: quevedo train [OPTIONS]

  Train the neural network.

  The training configuration and files must have been created by running the
  command `prepare`.  The weights obtained after training are stored in the
  network directory:
  `/<dataset>/networks/<network_name>/darknet_final.weights`.

Options:
  -c, --resume / --no-resume  Start training with existing weights from a
                              previous run
  --help                      Show this message and exit.
```

## `predict`

```txt
Usage: quevedo predict [OPTIONS]

  Get predictions for an image using the trained neural network.

Options:
  -i, --image PATH  Image to predict  [required]
  --help            Show this message and exit.
```

## `test`

```txt
Usage: quevedo test [OPTIONS]

  Compute evaluation metrics for a trained neural network.

  By default annotations marked as "test" (see train/test split) are used.
  Precision, recall and f-score are computed for each class, as well as global
  metrics (macro average). For more detailed statistics, the full predictions
  can be printed into a csv to be loaded into other software (like R).

Options:
  -p, --print / --no-print        Show results in the command line
  --results-csv / --no-results-csv
                                  Print results into a `results.csv` file in
                                  the network directory
  --results-json / --no-results-json
                                  Print results into a `results.json` file in
                                  the network directory
  --predictions-csv / --no-predictions-csv
                                  Print all predictions into a
                                  `predictions.csv` file in the network
                                  directory
  --on-train                      Test the network on the train set instead of
                                  the test one
  --help                          Show this message and exit.
```

## `web`

```txt
Usage: quevedo web [OPTIONS]

  Run a web interface to the dataset.

  The web application launched can be used to browse and manage the dataset
  files. Annotation pages are provided for both graphemes and logograms to
  allow visual annotation of objects. Very basic user management is also
  provided. Configuration can be written under the `web` key of the dataset
  configuration.

Options:
  -h, --host TEXT
  -p, --port TEXT
  -m, --mount-path TEXT     Mount path for the web application
  --browser / --no-browser  Launch browser with the web app
  -l, --language [es|en]    Language for the UI (default from config file)
  --help                    Show this message and exit.
```

## `run_script`

```txt
Usage: quevedo run_script [OPTIONS]

  Run a data processing script on dataset objects.

  The script should be in the 'scripts' directory of the dataset, and have a
  "process" method which will be called by Quevedo on each grapheme or
  logogram in the selected subsets.

Options:
  -s, --scriptname TEXT    Name of the script to run, without path or
                           extension  [required]
  -g, --grapheme-set TEXT  Process graphemes from these sets
  -l, --logogram-set TEXT  Process logograms from these sets
  --help                   Show this message and exit.
```
