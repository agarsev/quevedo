- Remember: images need to be 3 channel
- To add languages for the web, copy and edit a file in `/quevedo/web/static/i18n`

# TODO

I have removed the embedded steps in the experiments (train test split,
generation). Later we can put these again into some kind of chain/pipeline that
can include "experiments" (probably should rename) and other things (like
train test split, generation, and new preprocessing)

- Check that letterboxing is working with AlexeyAB's darknet
- Try again with grayscale images now that we use AlexeyAB
- Big section in documentation about config file

# PLAN

Right now we are moving to an architecture where symbols are very much like
"real" transcriptions, so that we can have the two types of nets (detect and
classify)

- [X] Make sure CNN works (previously, classifier symlink names not correctly generated)
- [X] Change symbol management to separate directories:
    - [X] class Annotation with enum Trans/Symbol
    - [X] add_images flag either trans or symbols
    - [X] train test split
    - [X] extract_symbols specifies from (tran) and to (symb), and preserves
        train/test mark
    - [X] generate from (symb) to (trans) (preserve train/test, mark somehow,
        remove get_generated), confirmation when overwriting. Marked all as
        "train", only use training symbols.
    - [X] remove extra things from experiment running
    - [X] Rename trans to tran everywhere
    - [X] get_generated no longer works, adapt experiments to include multiple
        subsets
    - [ ] dataset info!!
- [X] Adapt for classifier and new symbol arch
    - [X] adapt test and predict commands
    - [X] test with trained in server
- [X] Check CNN still works
- [O] Adapt web for symbols, and some extras
    - [X] en lista básica, también listar directorios de símbolos (bajo otro
        encabezado)
    - [X] urls using real/symbols
    - [X] Make new page (different from edit) for symbol editing (some code is
        probably the same, but not much). Edit.js remains, has meta and footer,
        imports annotation editor from either tran or symb
    - [ ] fix api (save, new, etc)
    - [X] In list.js show total number of annotations in a subset
    - [X] nice to have: add Copyright note, and app logo
- [ ] Add preproc option for experiments, create rotator script (in examples maybe)
   that uses rotation tab to realign symbols according to rotation tab
- [ ] Anotar vocab JM y entrenar incrementalmente como dice el folio

## test everything correct

I have changed function get_annotations and target is now a bit flag, so
re-check everything

- [ ] Check YOLO still works
- [ ] add images
- [ ] train test split
- [ ] extract
- [ ] generate, check only train used
- [ ] train and test


# ISSUES (move to github?)

- [ ] ALLOW Deleting entries (just move the last to the hole).
- [ ] RW permissions for users in web. Also user groups.
- [ ] Experiments should not be "checked" if not to be used. E.g when creating a
    dataset, you might change the tag schema, and then start adding images, but
    not adjust the experiment yet. It shouldn't then complain that the tag
    schema is wrong. maybe.
- [ ] In test, compute a confusion matrix (at least for classify) for deeper
    inspection
- [ ] If there are no folders under "real", the web interface should offer the
    default one even if the directory is not physically there.
- [ ] Use https://docs.python.org/3/library/collections.html#collections.Counter
    in test
- [ ] IMPORTANT Add license file, and license information for the dependencies.
    This must be shown in the web somehow too.

