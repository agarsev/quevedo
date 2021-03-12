- Remember: images need to be 3 channel
- To add languages for the web, copy and edit a file in `/quevedo/web/static/i18n`

# TODO

- Check that letterboxing is working with AlexeyAB's darknet
- Try again with grayscale images now that we use AlexeyAB

I have removed the embedded steps in the experiments (train test split,
generation). Later we can put these again into some kind of chain/pipeline that
can include "experiments" (probably should rename) and other things (like
train test split, generation, and new preprocessing)

# TO TEST

- [ ] add images
- [ ] train test split
- [ ] extract, generate, check only train used
- [ ] train and test

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
    - [ ] Rename trans to tran everywhere
    - [X] get_generated no longer works, adapt experiments to include multiple
        subsets
- [ ] Adapt for classifier and new symbol arch
    - [ ] adapt test and predict commands
    - [ ] test with trained in holstein
- [ ] Check CNN still works
- [ ] Adapt web for symbols, y ya que estamos más
    a. en lista básica, también listar directorios de símbolos (bajo otro
        encabezado)
    b. urls incluyen tran/symb
    c. (ya que estamos añadir COPYRIGHT)
    d. Contar en list.js el total de imágenes en un directorio.
    e. If there are no folders under "real", the web interface should offer the
        default one even if the directory is not physically there.
- [ ] Add preproc option for experiments, create rotator script (in examples maybe)
   that uses rotation tab to realign symbols according to rotation tab
- [ ] Anotar vocab JM y entrenar incrementalmente como dice el folio


# ISSUES (move to github?)

- [ ] ALLOW Deleting entries (just move the last to the hole).
- [ ] Experiments should not be "checked" if not to be used. E.g when creating a
    dataset, you might change the tag schema, and then start adding images, but
    not adjust the experiment yet. It shouldn't then complain that the tag
    schema is wrong. maybe.

