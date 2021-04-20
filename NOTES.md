- Remember: images need to be 3 channel
- To add languages for the web, copy and edit a file in `/quevedo/web/static/i18n`
- For classify, if a tag is missing, the grapheme is ignored (this is
    intentional, but maybe there should be a warning somewhere)

# -- NEXT --

- [ ] Refactor experiments (next section)
- [ ] Substitute cli flags -l/-g + -n set for -l set / -g set (less typing, more
    intuitive, more coherent with -f/-t in generate/extract, maybe change or
    allow there too)
 
## Refactor Experiments

- [X] Rename experiment -> network
- [ ] Load darknet inside network class so more than one can be used
- [ ] Network config relative path to their directory so can be ported (works
    for test, check for train)
- [ ] Predict load image from RAM (PIL image)
- [ ] train and test YOLO (new arch) 
- [ ] Add preproc option for experiments/pipelines, create rotator script (in
    examples maybe) that uses rotation tab to realign graphemes according to
    rotation tag.
- [ ] train and test CNN (new arch, with preproc)
- [ ] fix use experiment from web: select classify or detect depending on logo
    or graheme edition, and select tag to fill automatically

# -- BACKLOG --

Github issues are less 便利 than this file when you go solo 🤷.

## Bugs and improvements

- [ ] **IMPORTANT** Add license file, and license information for the dependencies.
    This must be shown in the web somehow too.
- [ ] **IMPORTANT** Rewrite README.md with latest info.
- [X] When the create command is aborted, if -D was given remove the directory
    so it can be done again. REJECTED
- [X] Experiments should not be "checked" if not to be used. E.g when creating a
    dataset, you might change the tag schema, and then start adding images, but
    not adjust the experiment yet. It shouldn't then complain that the tag
    schema is wrong. maybe. What we do is start with no tag specified, then the
    first one is used. Uncomment and change to use a different one.
- [ ] Use https://docs.python.org/3/library/collections.html#collections.Counter
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

Do this whenever the latest refactor is over 🤷

- [ ] Update Readme
- [ ] Big section in documentation about config file

## Experiments

- [ ] Incremental annotation
- [ ] Try moving additional data to coarse (YOLO) (eg rot, fill)
- [ ] Remember to record train/test split seeds for reproducibility

## Maybe

- [ ] Improve nets. Try again with grayscale images now that we use AlexeyAB
    fork, check letterboxing, try different configs, etc.

