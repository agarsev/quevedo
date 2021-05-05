- Remember: images need to be 3 channel
- To add languages for the web, copy and edit a file in `/quevedo/web/static/i18n`
- When training, if a file's corresponding tag is missing, the file is ignored.
    If multitag, only ignored if all tags are missing (not tested)

# -- NEXT --

- [O] Milestone: v1
    - [X] Refactor annotations (less undefined json, more python class)
        - [X] dataset
        - [X] web 
        - [X] classes
        - [X] extract_graphemes, generate
        - [X] network
    - [X] Allow annotation filtering for networks based on tags (eg different
        classify networks for different coarse-grain tags)
    - [X] Pipeline
    - [o] TODOs
        - [X] Sort subsets in `ds.get_subsets`
        - [X] Allow creating subsets in the web interface.
        - [ ] RW permissions for users in web. Also user groups.
        - [ ] Check ids in extract_graphemes
        - [ ] In test, compute a confusion matrix (at least for classify) for deeper
            inspection. Better yet, optionally output predictions + ground truth to a
            csv, stats etc. can be better computed with R later.
        - [ ] Allow restarting training with latest weights if weights directory exists,
            or maybe recover gracefully from Ctrl+C when training, to allow interrupt
            before overfitting etc. Or both.
        - [ ] Fix/rework example scripts in `examples`
    - [ ] Docs

# -- DOCS --

- [ ] Add license file, and license information for the dependencies.
    This must be shown in the web somehow too.
- [ ] Rewrite README.md with latest info.
- [ ] Write the user guide
    - [ ] Concepts, dataset structure, file formats
    - [ ] CLI usage
    - [ ] Config file
    - [ ] Dev guide

# -- BACKLOG --

Maybe for next version

- [ ] In split command, add a "k-set" to offset split index, which combined
    with the seed can allow for cross-validation
- [ ] Auto-save changes in the web interface if enabled in the config file
    (nowadays people aren't so used to clicking save)
- [ ] Remove "saved" message when doing changes (inconsistent)
- [ ] Allow deleting entries in web (just move the last to the hole). Maybe
    add `delete` in cli too?
- [ ] Filter/search annotations in listing according to some tag(s).
- [ ] Autosuggest values for tagging.
- [ ] Mobile interface for the web app. Maybe integrate with camera/scan app,
    make quevedo a target for "sharing" (uploading) images.
- [ ] Annotated/not annotated status based on a custom checkbox, useful for
    revision (or right now, most annotated but need to redo, need to know where
    I am. and the number based is useless in multi tag)
- [ ] Improve nets. Try again with grayscale images now that we use AlexeyAB
    fork, check letterboxing, try different configs, etc.
- [ ] When scripts modify images, don't save it automatically, but return it
    (ie return modified_tags, modified_img) and then it is `run_script` that
    saves the image to the appropriate path. Then, the updated image can be sent
    to the web interface to be previewed, and if want to save it sent back to
    the server on "save".
