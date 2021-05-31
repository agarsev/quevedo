# Roadmap

## Version 1

- [X] License
    - [X] Add license file
    - [X] Add OSL 3 notice to own source (after copyright)
    - [X] Add license information for the dependencies, and link to this info in
        the web interface.
- [X] README.md 
    - [X] Overview
    - [X] Authorship
    - [X] Installation
    - [X] How to install extras
    - [X] Usage
- [X] Docs
    - [X] Concepts
    - [X] Networks
    - [X] Config file
    - [X] CLI
    - [X] Web application
    - [X] Developer guide
        - [X] API Reference
        - [X] Use as library and user scripts
    - [X] User guide: example of shell use, with git and DVC
- [ ] TODOs
- [ ] Rework examples
- [X] Deploy documentation
- [X] Make a toy dataset and add to release so people can play even if they
    don't have data.
- [ ] Publish
    - [ ] Github Release -> add toy dataset
    - [ ] Publish to PyPI

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
