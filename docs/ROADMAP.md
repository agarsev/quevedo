# Roadmap

Don't remove elements from here until version released, then use this file to
populate the changelog.

## Next

Version 1.1 + Dataset version 1 (not compatible with 0)

- [ ] Move tags from a list to a defaultdict
    - [ ] Grapheme
    - [ ] BoundGrapheme
    - [ ] Web interface
    - [ ] Nets
    - [ ] Dataset versioning and migration (version 1 versus "0", no version)
- [ ] Net config improvements
    - [ ] Configure max epochs, size, etc. More params in general.
    - [ ] Improve multi tags. Joining with underscore problem if tags have
        underscores. Maybe format strings? Choose joining char? Use exotic
        unicode?
- [ ] Improve train/test set. Instead of "set", "slice"/"division", and
    it's an integer. Orthogonal dimension to subsets. Slices to include
    can be chosen somehow, as params or something (think DVC). This
    enables cross-validation while preserving "slice" through extract
    etc. Or maybe use lists of files (ala darknet) that can be tracked by
    git/dvc. A directory for "splits", these splits list annotations, can be
    shared by different nets.
- [ ] Web interface improvements
    - [ ] Filter/search annotations in listing according to some tag(s).
    - [ ] Autosuggest values for tagging.
    - [ ] Remove "saved" message when doing changes (inconsistent)
    - [ ] Instead of a "check" for annotated/not annotated, custom "flags" in
        config.toml that are checkboxes in meta and can be toggled in web interface.

## Backlog

- [ ] When scripts modify images, don't save them, but return that it has been
    modified (ie return modified_tags, modified_img) and then it is `run_script`
    that saves the image to the appropriate path. Coversely, in the web
    interface the updated image can be sent to the frontend to be previewed, and
    if they want to save it send it back to the server on "save". The
    complication is that the image is now frontend state, not just a src link.
- [ ] Allow deleting entries in web (just move the last to the hole). Maybe
    add `delete` in cli too?
- [ ] Mobile interface for the web app. Maybe integrate with camera/scan app,
    make quevedo a target for "sharing" (uploading) images.
- [ ] Web user improvements: groups and recording annotator in json.
- [ ] Improve nets. Try again with grayscale images now that we use AlexeyAB
    fork, check letterboxing, try different configs, etc. Some of this can be
    done by improving the python code that access the darknet dll (eg the
    channels) and some might be better to do ourselves (eg letterboxing and
    resizing). Maybe migrate to tensorflow and keras if we get hardware where to
    test it.
