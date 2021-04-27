- Remember: images need to be 3 channel
- To add languages for the web, copy and edit a file in `/quevedo/web/static/i18n`
- When training, if a file's corresponding tag is missing, the file is ignored

# -- NEXT --

- [X] Refactor experiments (next section)
- [X] Add Quevedo notice to default_config.toml
- [X] Allow test on train set
- [ ] Substitute cli flags -l/-g + -n set for -l set / -g set (less typing, more
    intuitive, more coherent with -f/-t in generate/extract, maybe change or
    allow there too) and test changed:
    - [ ] split
- [ ] Whole pipeline script detection + classification -> can be called from
    web, how? Maybe scripts in the dataset scripts folder, if start with
    grapheme/logogram or some convention, can be called from web on the current
    annotation.
- [ ] Try and see if we can get 'predict' to load image from RAM (PIL image)
    instead of fs.
 
## Refactor Experiments

- [X] Rename experiment -> network
- [X] Make Network class, subclassed by Detector and Classifier, add factory
- [X] Network config relative path to their directory so can be ported (works
    for test, check for train)
- [X] Load darknet inside network class so more than one can be used
    - [X] train
    - [X] test
- [X] train and test CNN 
- [X] train and test YOLO
- [X] create script for grapheme processing. Call it after extract. For our SW dataset, create script that
    rotates according to ROT tag.
- [X] allow tag combinations for pipelines (get_tag not only index, but can concat eg)
- [X] train and test CNN
- [X] fix use experiment from web
    - [X] for logograms, offer detection nets, for graphemes, classifiers
    - [X] fix how to interpret results with combined tags

# -- BACKLOG --

Github issues are less 便利 than this file when you go solo 🤷.

## Bugs and improvements

- [ ] **IMPORTANT** Add license file, and license information for the dependencies.
    This must be shown in the web somehow too.
- [ ] **IMPORTANT** Rewrite README.md with latest info.
- [ ] If there are no annotation folders, the web interface should offer the
    default one even if the directory is not physically there. Or maybe allow
    creating subsets in the web interface.

## Features

- [ ] Allow restarting training with latest weights if weights directory exists,
    or maybe recover gracefully from Ctrl+C when training, to allow interrupt
    before overfitting etc. Or both.
- [ ] Allow annotation filtering for networks based on tags (eg different
    classify networks for different coarse-grain tags)
- [ ] In split command, add a "k-set" to offset split index, which combined
    with the seed can allow for cross-validation
- [ ] Auto-save changes in the web interface if enabled in the config file
    (nowadays people aren't so used to clicking save)
- [ ] Remove "saved" message when doing changes (inconsistent)
- [ ] Allow deleting entries in web (just move the last to the hole). Maybe
    add `delete` in cli too?
- [ ] Filter/search annotations in listing according to some tag(s).
- [ ] RW permissions for users in web. Also user groups.
- [ ] In test, compute a confusion matrix (at least for classify) for deeper
    inspection
- [ ] Autosuggest values for tagging.
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

