# 2020-04-08 Antonio F. G. Sevilla <afgs@ucm.es>

import click
import json

@click.command()
@click.pass_obj
def make_yolo_files (dataset):
    ''' Creates the darknet / yolo bounding box annotation files for the
    transcriptions in the `real` directory of the dataset. It uses the
    json file annotations created by the tagger, so this must have been done
    first. '''

    real_d = dataset.path / 'real'

    for an in real_d.glob('*.json'):
        annotation = json.loads(an.read_text())
        bboxes = [ "{} {} {} {} {}".format(s['name'], *s['box'])
                for s in annotation['symbols'] ]
        an.with_suffix(".txt").write_text("\n".join(bboxes))
