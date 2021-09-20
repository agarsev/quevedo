# Changelog

## v1.1

### New dataset version 1

Before, Quevedo datasets were not versioned. Now, a field has been added to the
`config.toml` file to track the Quevedo dataset schema, and a `migrate` command
has been added to let users upgrade datasets to new versions.

Some of the following additions are incompatible changes to dataset
functionality and annotation files which have made this version upgrading
necessary.

### Tags are now a dictionary

Grapheme tags (both free and bound) are now represented with a dictinary, with
keys the names in the dataset `tag_schema`. This makes Annotation objects easier
to use in custom code. The change affects both the library code and the files on
disk, hence the migration.

### Splitting now works differently

Instead of assigning annotations to either a train or test split, they are
assigned to a "fold". Groups of folds can then be defined as being available for
train or for test (or none). This is also an incompatible change to annotation
code and file representation. Old partitions will be lost, so after migration
you will need to run the `split` command again.

### Net configuration improvements

- Detection networks can now have `width` and `height` parameters to tune
    network input size.
- All networks can now have a `max_batches` parameter to customize when to stop
    training the net. This can serve to prevent overfitting and shorten training
    times.

### Annotation flags

A new option "flags" has been added to the `config.toml` file. These flags are
matadata values just like those in `meta_tags`, so assigned to both Logograms
and Free Graphemes. The difference is that they are presented as checkboxes in
the web interface, and shown as icons in annotation listings. This can serve to
quickly mark annotations for annotators, for example if some have dubious or
problematic tags, need some other kind of attention, or simply you want to keep
track of them.

### Other

- When building the tag map for darknet, user tags are combined using the ASCII
    FS character instead of "_", which can be problematic if tag values in the
    dataset contain "_". This is an internal change and user code and data
    should not be affected.
- The `dataset.get_network` method now returns the same `Network` object if
    called many times with the same network name. This helps save memory, which
    in the case of neural networks can be crucial, without requiring the user to
    keep the network in their own variable.
- The web interface now can be used with touch on mobile devices.
