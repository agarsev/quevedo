# 2022-02-09 Antonio F. G. Sevilla <afgs@ucm.es>
# Licensed under the Open Software License version 3.0
#
# This script merges graphemes (including tags and bounding boxes) which are
# connected by "partof" edges

from quevedo import Logogram, BoundGrapheme, Dataset


def merge_boxes(a, b):
    left = min(a[0]-a[2]/2, b[0]-b[2]/2)
    right = max(a[0]+a[2]/2, b[0]+b[2]/2)
    top = min(a[1]-a[3]/2, b[1]-b[3]/2)
    bottom = max(a[1]+a[3]/2, b[1]+b[3]/2)
    w = right - left
    h = bottom - top
    return [left + w/2, top + h/2, w, h]


def merge_graphemes(a: BoundGrapheme, b: BoundGrapheme):
    for e in a.inbound():
        e.end = b
    for e in a.outbound():
        e.start = b
    b.tags.update(a.tags)
    b.box = merge_boxes(a.box, b.box)


def process(l: Logogram, ds: Dataset):
    oldedges = [*l.edges]
    for e in oldedges:
        if e.tags['FUNC'] != 'partof':
            continue
        l.edges.remove(e)
        merge_graphemes(e.start, e.end)
        l.graphemes.remove(e.start)
    return True  # We have updated the annotation
