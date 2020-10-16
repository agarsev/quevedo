# 2020-09-14 Antonio F. G. Sevilla <afgs@ucm.es>

import click
import json


def migrate_annotations(dataset):
    for an in (dataset.path / 'real').glob('*.json'):
        annotation = json.loads(an.read_text())
        # From single annotation to table annotation
        for s in annotation['symbols']:
            if 'name' in s:
                name = s.pop('name')
                s['tags'] = [name]
        an.write_text(json.dumps(annotation))


@click.command()
@click.pass_obj
def migrate(dataset):
    migrate_annotations(dataset)
