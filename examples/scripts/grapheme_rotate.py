# 2021-05-31 Antonio F. G. Sevilla <afgs@ucm.es>
# Licensed under the Open Software License version 3.0
#
# This script rotates graphemes so that they are upright. Please note that image
# modification in the web interface is not a consistent experience due to
# caches, so this script is better run from the command line.

from PIL import Image
from quevedo import Dataset, Grapheme


# The process function allows this script to be used by Quevedo
def process(a: Grapheme, ds: Dataset):

    angles = a.tags.get('ROTATION', 0)

    if angles == 0:
        return False  # Nothing to change

    else:
        image: Image = a.image
        image.rotate(angles, expand=True)
        image.save()
        a.tags['ROTATION'] = 0
        return True  # Save the new rotation
