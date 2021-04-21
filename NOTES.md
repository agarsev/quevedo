- Remember: images need to be 3 channel
- To add languages for the web, copy and edit a file in `/quevedo/web/static/i18n`
- When training, if a files corresponding tag is missing, the file is ignored

# -- NEXT --

- [ ] Refactor experiments (next section)
- [ ] Substitute cli flags -l/-g + -n set for -l set / -g set (less typing, more
    intuitive, more coherent with -f/-t in generate/extract, maybe change or
    allow there too)
- [ ] Add postprocessing to networks too (eg. tags that can be filled from
    rules, maybe some error correction)
 
## Refactor Experiments

- [X] Rename experiment -> network
- [X] Make Network class, subclassed by Detector and Classifier, add factory
- [X] Network config relative path to their directory so can be ported (works
    for test, check for train)
- [X] Load darknet inside network class so more than one can be used
    - [X] train
    - [X] test
- [X] train and test CNN 
- [ ] train and test YOLO
- [ ] Add preproc option for networks. This preproc should return tag name (for
    processed/mixed tags) and can modify the train file (eg. rotate). It can't
    be a link, then, should be a copy. For our SW dataset, create script that
    rotates according to ROT tag and combines SHAPE and FILL.
- [ ] train and test CNN (with preproc)
- [ ] fix use experiment from web: select classify or detect depending on logo
    or graheme edition, select tag to fill automatically, extract graphemes for
    classification, apply pre processing...
- [ ] Predict load image from RAM (PIL image)

# -- BACKLOG --

Github issues are less 便利 than this file when you go solo 🤷.

## Bugs and improvements

- [ ] **IMPORTANT** Add license file, and license information for the dependencies.
    This must be shown in the web somehow too.
- [ ] **IMPORTANT** Rewrite README.md with latest info.
- [X] Use https://docs.python.org/3/library/collections.html#collections.Counter
    in test
- [ ] If there are no annotation folders, the web interface should offer the
    default one even if the directory is not physically there. Or maybe allow
    creating subsets in the web interface.

## Features

- [ ] Auto-save changes in the web interface if enabled in the config file
    (nowadays people aren't so used to clicking save)
- [ ] Remove "saved" message when doing changes (inconsistent)
- [ ] Allow deleting entries in web (just move the last to the hole). Maybe
    add `delete` in cli too?
- [ ] Allow restarting training with latest weights if weights directory exists.
- [ ] Filter/search annotations in listing according to some tag(s).
- [ ] RW permissions for users in web. Also user groups.
- [ ] In test, compute a confusion matrix (at least for classify) for deeper
    inspection
- [ ] Autosuggest values for tagging.
- [ ] Add a configurable preprocessing module that applies common image
    enhancement to data, for example increasing contrast, reducing noise,
    whatever. This should be enabled/disabled in config. Maybe there can be a flag in
    `add_images` that decides whether to process added images. This preprocessing
    should be used when predicting new instances (also when testing, but images
    there have already been added and therefore processed). 
- [ ] Mobile interface for the web app. Maybe integrate with camera/scan app,
    make quevedo a target for "sharing" (uploading) images.
- [ ] Annotated/not annotated status based on a custom checkbox, useful for
    revision (or right now, most annotated but need to redo, need to know where
    I am. and the number based is useless in multi tag)

## Documentation

- [ ] Document whenever the latest refactor is over 🤷
- [ ] Big section in documentation about config file

## Experiments

- [ ] Incremental annotation
- [ ] Try moving additional data to coarse (YOLO) (eg rot, fill)
- [ ] Remember to record train/test split seeds for reproducibility

## Maybe

- [ ] Improve nets. Try again with grayscale images now that we use AlexeyAB
    fork, check letterboxing, try different configs, etc.

