# Roadmap

## Version 1

Remaining: documentation

- [ ] Add license file, and license information for the dependencies.
    This must be shown in the web somehow too.
- [ ] Rewrite README.md with latest info.
- [ ] Write the user guide
    - [ ] Concepts, dataset structure, file formats
    - [ ] CLI usage
    - [ ] Config file
- [ ] Examples
    - [ ] Scripts for use of quevedo as library and for use as internal script
        (fixing tags, changing images, etc.)
    - [ ] Example notebooks
    - [ ] Example R notebook computing eg. confusion matrix from test and other
        stats
- [ ] Developer guide

Notes to document:

- images need to be 3 channel
- To add languages for the web, copy and edit a file in `/quevedo/web/static/i18n`
- When training, if a file's corresponding tag is missing, the file is ignored.
    If multitag, only ignored if all tags are missing (not tested)

## Future

- [ ] Improve train/test set. Instead of "set", "slice"/"division", and
    it's an integer. Orthogonal dimension to subsets. Slices to include
    can be chosen somehow, as params or something (think DVC). This
    enables cross-validation while preserving "slice" through extract
    etc.
- [ ] Filter/search annotations in listing according to some tag(s).
- [ ] Autosuggest values for tagging.
- [ ] Remove "saved" message when doing changes (inconsistent)
- [ ] Instead of a "check" for annotated/not annotated, custom "flags" in
    config.toml that are checkboxes in meta and can be toggled in web interface.

## Backlog

- [ ] Allow deleting entries in web (just move the last to the hole). Maybe
    add `delete` in cli too?
- [ ] Auto-save changes in the web interface if enabled in the config file
    (nowadays people aren't so used to clicking save)
- [ ] Mobile interface for the web app. Maybe integrate with camera/scan app,
    make quevedo a target for "sharing" (uploading) images.
- [ ] Web user groups.
- [ ] When scripts modify images, don't save it automatically, but return it
    (ie return modified_tags, modified_img) and then it is `run_script` that
    saves the image to the appropriate path. Then, the updated image can be sent
    to the web interface to be previewed, and if they want to save it send it
    back to the server on "save". The only complication is that the image is now
    frontend state, not just a src link.
- [ ] Improve nets. Try again with grayscale images now that we use AlexeyAB
    fork, check letterboxing, try different configs, etc. Some of this can be
    done by improving the python code that access the darknet dll (eg the
    channels) and some might be better to do ourselves (eg letterboxing and
    resizing)
