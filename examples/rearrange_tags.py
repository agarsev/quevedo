# 2021-02-22 Antonio F. G. Sevilla <afgs@ucm.es>
# Licensed under the Open Software License version 3.0
#
# Example of a script that moves tags one position down in a dataset and subset
# (sudbir). This can be useful if you need to add a new tag to the tag schema,
# and *really* want it to be first (otherwise, just append it to the tag
# schema).

import sys

from quevedo.dataset import Dataset
from quevedo.annotation import Target


if __name__ == '__main__':
    ds = Dataset(sys.argv[1])
    for t in ds.get_annotations(Target.LOGO, sys.argv[2]):
        for s in t.anot.get('graphemes', []):
            s['tags'] = [''] + s['tags']
        t.save()