- Remember: images need to be 3 channel

# TODO

- IMPORTANT: sort obj.names file, otherwise datasets not portable (at all, see
    item below about prepare)
- Rename tagger to "web" (simpler)
- Move experiment configuration to info.yaml. Review and remake "create" and
    dataset.py
- Use latest weight to restart training if weights directory exists. 
- Create `run` command that runs all commands for an experiment
- When moving a dataset, `prepare` has to be called too before testing (so
    rearchitecture that, and don't call it `pre_train`).
- Ship different yolo config files and allow user to select for each experiment
    (either in config or in prepare or something)
- Tagger Undo/Redo (use reducer for state in webapp?)
- Documentation for dataset/annotation format !IMPORTANT
- Internationalization (ES and EN)
- Experiments with mixed tags
- Add option to change detection threshold in test and compare
- Upload transcriptions from the tagger list interface (maybe some image
    normalization there?)
- Use alexnet for symbols
- Check that letterboxing is working with AlexeyAB's darknet, and try again
  grayscale images
- Include improve.sh as python code (PIL) so that it can be used for test etc.
- Maybe move all hardcoded paths in the dataset to the Dataset class as properties.
- Use bash complete https://click.palletsprojects.com/en/7.x/bashcomplete/
- Allow separation of real transcriptions in directories (e.g. to keep different
    sources separate)
