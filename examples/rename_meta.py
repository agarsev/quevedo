# 2021-02-22 Antonio F. G. Sevilla <afgs@ucm.es>
#
# Example of a script that changes meta keys names. For example if you
# misspelled them in a previous script like I did... Or maybe if you realize a
# key name is confusing and want to improve it, while keeping the values
# already stored.

import sys

from quevedo.dataset import Dataset
from quevedo.annotation import Target

translation = {
    'worng_name': 'correct_name',
    'bad_key': 'better_key',
}


if __name__ == '__main__':
    ds = Dataset(sys.argv[1])
    for t in ds.get_annotations(Target.LOGO):
        meta: dict = t.anot.get('meta')
        for orig, trad in translation.items():
            if orig in meta:
                meta[trad] = meta[orig]
                del meta[orig]
        t.save()
