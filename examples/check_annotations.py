# 2021-09-20 Antonio F. G. Sevilla <afgs@ucm.es>
# Licensed under the Open Software License version 3.0
#
# Check annotations in the dataset, warn about wrong ones or fix those that can
# be automatically fixed.

from quevedo import Annotation, Grapheme, Target, Dataset


# Possible values for the tag "SHAPE"
SHAPES = {
    'ARROW': ('straight', 'curve', 'zigzag'),
    'STAR': ('5p', '6p', '7p', '8p'),
}

# Possible values for the tag "FILL" (common to all shapes)
FILLS = ('black', 'gray', 'white')

# We know the old annotation was this, so we can fix it
FIX_STAR = {
    'five': '5p', 'six': '6p', 'seven': '7p', 'eight': '8p'
}


# Check that this grapheme has been annotated with this obligatory tag, and
# optionally that the value is one of the acceptable ones
def check_obligatory(a: Grapheme, name, tag, valid=None):
    v = a.tags.get(tag)
    if v is None or v == '':
        print("Missing {} in {}".format(tag, name))
    elif valid is not None and v not in valid:
        print("Wrong {} '{}' in {}".format(tag, v, name))


# Check that this annotation has not been annotated with this tag. If the value
# is one that might have been left over (None, '', or in maybe) we just delete
# it, otherwise warn.
def check_extraneous(a: Grapheme, name, tag, maybe=()):
    if tag in a.tags:
        v = a.tags[tag]
        if v is None or v == '' or v in maybe:
            del a.tags[tag]
            return True
        else:
            print("Wrong {} '{}' in {}".format(tag, v, name))
    return False


def check_grapheme(a: Grapheme, name):
    changed = False

    # CLASS is a tag that determines what other tags are necessary/obligatory
    cl = a.tags.get('CLASS')
    if cl is None or cl == '':
        print("Missing CLASS in {}".format(name))
        return False

    if cl == 'ARROW':
        check_obligatory(a, name, 'SHAPE', SHAPES['ARROW'])
        check_obligatory(a, name, 'FILL', FILLS)
        changed |= check_extraneous(a, name, 'BORDER')
    elif cl == 'STAR':
        sh = a.tags.get('SHAPE')
        if sh in SHAPES['STAR']:
            pass
        elif sh in FIX_STAR:
            a.tags['SHAPE'] = FIX_STAR[sh]
            changed = True
        else:
            print("Wrong SHAPE '{}' in {} in {}".format(sh, cl, name))
        check_obligatory(a, name, 'FILL', FILLS)
        changed |= check_extraneous(a, name, 'BORDER')
    elif cl == 'TEXT':
        # TEXT can have arbitrary values for SHAPE
        check_obligatory(a, name, 'SHAPE')
        check_obligatory(a, name, 'FILL', FILLS)
        check_obligatory(a, name, 'BORDER', ('black', 'white'))
    else:
        print("Extraneous CLASS {} in {}".format(cl, name))
    return changed


# Main function, ran for every annotation given to `run_script`
def process(a: Annotation, _: Dataset):
    changed = False
    if a.target == Target.LOGO:
        for g in a.graphemes:
            changed |= check_grapheme(g, a.json_path)
    else:
        changed |= check_grapheme(a, a.json_path)
    if changed:
        print("Fixed {}".format(a.json_path))
    return changed
