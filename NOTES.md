- Remember: images need to be 3 channel

# Right now

- Annotation tables: in train.py and test.py there is "get_tag". It should be
    made more general/configurable to use other tags than the first column. This
    should also be reflected somehow in the tagger when getting the "auto"
    annotations.
- Must adapt symbol generation to tabular annotation too

# TODO

- When moving a dataset, `prepare` has to be called too before testing (so
    rearchitecture that, and don't call it `pre_train`). Also be careful about
    order of `obj.names` file. probably should sort tags beforehand to be
    deterministic.
- Tagger Undo/Redo (use reducer for state in webapp?)
- Document dataset/annotation format !IMPORTANT
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
