# 2021-08-03 Antonio F. G. Sevilla <afgs@ucm.es>
# Licensed under the Open Software License version 3.0

import click
import toml

from quevedo.dataset import Dataset, CURRENT_CONFIG_VERSION
from quevedo.annotation import Grapheme, Target


def _migrate_one(dataset: Dataset):
    '''Migrate dataset from version 0 to 1.'''
    # Add version field to config
    dataset.config['config_version'] = 1
    schema = dataset.config['tag_schema']

    # Change annotation tags from list to dict.
    def list_to_dict(a: Grapheme):
        if (not isinstance(a.tags, list)):
            return
        old_tags = a.tags
        a.tags = {}
        for i in range(min(len(schema), len(old_tags))):
            a.tags[schema[i]] = old_tags[i]
    for a in dataset.get_annotations():
        if a.target == Target.LOGO:
            for g in a.graphemes:
                list_to_dict(g)
        else:
            list_to_dict(a)
        a.save()
    click.echo("Train/test splits no longer apply, now folds are used. Please"
        " read the documentation, and run the `split` command again")

    # Add split configuration to config
    dataset.config['folds'] = 10
    dataset.config['train_folds'] = [0, 1, 2, 3, 4, 5, 6, 7]
    dataset.config['test_folds'] = [8, 9]

    # Add "flags"
    dataset.config['flags'] = {"done": "✔️", "problem": "⚠️", "notes": "📝"}


def _migrate_two(dataset: Dataset):
    '''Migrate dataset from version 1 to 2.'''
    dataset.config['config_version'] = 2
    dataset.config['g_tags'] = dataset.config['tag_schema']
    dataset.config['l_tags'] = []
    dataset.config['e_tags'] = []
    del dataset.config['tag_schema']
    if 'default' in dataset.config:
        del dataset.config['default']


@click.command('migrate')
@click.pass_obj
def migrate(obj):
    '''Upgrades a dataset config and data to the latest version.

    DANGER! This will change your annotations. Please have a backup of your data
    in case something goes wrong.'''
    dataset = obj['dataset']
    dataset._config = toml.loads(dataset.config_path.read_text())
    version = dataset.config.get('config_version', 0)

    if version == CURRENT_CONFIG_VERSION:
        raise SystemExit("This dataset is already at the latest config version ({})".format(CURRENT_CONFIG_VERSION))

    if version < 1:
        _migrate_one(dataset)
    if version < 2:
        _migrate_two(dataset)

    dataset.config_path.write_text("# This file is a Quevedo dataset configuration file. Find more at:\n" +
                                   "# https://www.github.com/agarsev/quevedo\n\n" +
                                   toml.dumps(dataset.config))
    click.echo("Upgraded dataset from version {} to {}".format(
        version, CURRENT_CONFIG_VERSION))
