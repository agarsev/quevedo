- Remember: images need to be 3 channel
- To add languages for the web, copy and edit a file in `/quevedo/web/static/i18n`

# -- NEXT --

- [ ] Rename symbol to grapheme

## Test new transcription / grapheme arch

Do these tests while creating a new dataset that can be used to work on
experiments in the next iteration.

- [ ] add images
- [ ] train test split
- [ ] extract
- [ ] generate, check only train used
- [ ] annotate graphemes in the web app
- [ ] train and test YOLO (pre-experiment refactor)
- [ ] train and test CNN (pre-experiment refactor)
 
## Refactor Experiments

I have removed the embedded steps in the experiments (train test split,
generation). Later we can put these again into some kind of chain/pipeline that
can include "experiments" (probably should rename) and other things (like
train test split, generation, and new preprocessing). See next iteration for
experiment integration into pipeline.

- [ ] Think of better name for experiments, and implement a pipeline arch.
- [ ] train and test YOLO (new arch) 
- [ ] Add preproc option for experiments/pipelines, create rotator script (in
    examples maybe) that uses rotation tab to realign graphemes according to
    rotation tag.
- [ ] train and test CNN (new arch, with preproc)
- [ ] fix use experiment from web: select classify or detect depending on tran
    or graheme edition, and select tag to fill automatically

## Pipeline

Steps/Experiments should work with lists. For each element in the list, they
produce an element (CNN, preproc) or a list (YOLO, multirotate). A step can
flatten sublists (e.g. keep all detections from YOLO) or convert them into
single elements (e.g. use softmax to keep the best prediction from CNN), or just
pass-through (preprocessing). The final step takes the list and converts it into
json or something that can be output.


# -- BACKLOG --

Github issues are less 便利 than this file when you go solo 🤷.

## Bugs and improvements

- [ ] IMPORTANT Add license file, and license information for the dependencies.
    This must be shown in the web somehow too.
- [ ] Rewrite README.md with latest info.
- [ ] When the create command is aborted, if -D was given remove the directory
    so it can be done again.
- [ ] Experiments should not be "checked" if not to be used. E.g when creating a
    dataset, you might change the tag schema, and then start adding images, but
    not adjust the experiment yet. It shouldn't then complain that the tag
    schema is wrong. maybe.
- [ ] Use https://docs.python.org/3/library/collections.html#collections.Counter
    in test
- [ ] If there are no folders under "real", the web interface should offer the
    default one even if the directory is not physically there.

## Features

- [ ] Auto-save changes in the web interface if enabled in the config file
    (nowadays people aren't so used to clicking save)
- [ ] Allow deleting entries in web (just move the last to the hole). Maybe
    add `delete` in cli too?
- [ ] Allow restarting training with latest weights if weights directory exists.
- [ ] RW permissions for users in web. Also user groups.
- [ ] In test, compute a confusion matrix (at least for classify) for deeper
    inspection
- [ ] Add a configurable preprocessing module that applies common image
    enhancement to data, for example increasing contrast, reducing noise,
    whatever. This should be enabled/disabled in config. Maybe there can be a flag in
    `add_images` that decides whether to process added images. This preprocessing
    should be used when predicting new instances (also when testing, but images
    there have already been added and therefore processed). 
- [ ] Mobile interface for the web app. Maybe integrate with camera/scan app,
    make quevedo a target for "sharing" (uploading) images.

## Documentation

- [ ] Do this whenever the latest refactor is over 🤷
- [ ] Big section in documentation about config file

## Maybe

- [ ] Improve nets. Try again with grayscale images now that we use AlexeyAB
    fork, check letterboxing, try different configs, etc.

