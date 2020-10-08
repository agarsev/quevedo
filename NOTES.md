- Remember: images need to be 3 channel

# Right now

- Move to multi experiment arch. In each dataset, there is a directory
    "experiments". There are, for each experiment, a yaml file with
    configuration, and a directory with results. Most previous things should now
    take this into account, a new cli option "experiment" which to use.
- TO ADAPT:
    * extract_symbols
    * generate
    * darknet use
    * tagger auto annotate

# TODO

- When moving a dataset, `prepare` has to be called too before testing (so
    rearchitecture that, and don't call it `pre_train`). Also be careful about
    order of `obj.names` file. probably should sort tags beforehand to be
    deterministic.
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
