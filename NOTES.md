- Remember: images need to be 3 channel
- To add languages for the web, copy and edit a file in `/quevedo/web/static/i18n`
- When training, if a file's corresponding tag is missing, the file is ignored.
    If multitag, only ignored if all tags are missing (not tested)

# -- NEXT --

- [o] Milestone: v1
    - [X] Refactor annotations (less undefined json, more python class)
        - [X] dataset
        - [X] web 
        - [X] classes
        - [X] extract_graphemes, generate
        - [X] network
    - [X] Allow annotation filtering for networks based on tags (eg different
        classify networks for different coarse-grain tags)
    - [ ] Pipeline
    - [ ] TODOs
    - [ ] Docs

# -- PIPELINE --

- [ ] Call scripts from web (Annotation -> Annotation) How to decide which
    scripts can be called? Name convention? Exported function name?
- [ ] Script that given an annotation with detections, classifies the graphemes
    - [ ] Move functionality to extract graphemes to grapheme annotation class
    - [ ] Try and see if we can get 'predict' to load image from RAM (PIL image)
        instead of fs.
- [ ] Script that uses the above script to perform detection + classification on
    raw image (external/library use)
 
## -- TODO --

- [ ] In test, compute a confusion matrix (at least for classify) for deeper
    inspection
- [ ] If there are no annotation folders, the web interface should offer the
    default one even if the directory is not physically there. Or maybe allow
    creating subsets in the web interface.
- [ ] Sort subsets in the web interface
- [ ] Allow restarting training with latest weights if weights directory exists,
    or maybe recover gracefully from Ctrl+C when training, to allow interrupt
    before overfitting etc. Or both.
- [ ] RW permissions for users in web. Also user groups.
- [ ] Fix/rework example scripts in `examples`

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
