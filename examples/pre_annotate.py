# 2021-05-31 Antonio F. G. Sevilla <afgs@ucm.es>
# Licensed under the Open Software License version 3.0
#
# This script fills in some annotation data that can be automatically
# determined. Useful right after import.

from datetime import date
from quevedo import Annotation, Dataset, Target


# Our custom logic to get tags from the filename
def tags_from_filename(filename: str):

    # We know that the file names of our source data are arranged like this
    tags = filename.split('_')

    # We can change some of the values to fit our annotation schema
    if tags[0] == 'something':
        tags[0] = 'some other thing'

    return tags


# The process function allows this script to be used by Quevedo
def process(a: Annotation, ds: Dataset):

    if a.meta['author'] is not None:
        return False  # We don't want to modify this annotation

    a.meta['annotation_date'] = date.today()
    a.meta['author'] = 'automatic'

    if a.target == Target.GRAPH:
        # The original filename is kept by `add_images`
        a.tags = tags_from_filename(a.meta['filename'])

    # We have updated the annotation, so return True for Quevedo to save it
    return True


# We can also call the script ourselves
if __name__ == '__main__':

    import sys

    if len(sys.argv) != 2:
        print(f'Usage: {sys.argv[0]} path/to/dataset')
        exit(0)

    ds = Dataset(sys.argv[1])
    for a in ds.get_annotations(Target.GRAPH):
        modified = process(a, ds)
        if modified:
            a.save()
