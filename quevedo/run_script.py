# 2021-04-26 Antonio F. G. Sevilla <afgs@ucm.es>
# Licensed under the Open Software License version 3.0

import click
import importlib.util

from quevedo import Dataset, Target


# Adapted from @wecsam
# https://stackoverflow.com/questions/4383571/importing-files-from-different-folder
def module_from_file(module_name, file_path):
    file = (file_path / module_name).with_suffix('.py')
    spec = importlib.util.spec_from_file_location(module_name, file)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@click.command("run_script")
@click.option('--scriptname', '-s', required=True,
              help="Name of the script to run, without path or extension")
@click.option('--grapheme-set', '-g', multiple=True,
              help="Process graphemes from these sets")
@click.option('--logogram-set', '-l', multiple=True,
              help="Process logograms from these sets")
@click.pass_obj
def run_script(obj, scriptname, grapheme_set, logogram_set):
    '''Run a data processing script on dataset objects.

    The script should be in the 'scripts' directory of the dataset, and have a
    "process" method which will be called by Quevedo on each grapheme or
    logogram in the selected subsets.'''

    ds: Dataset = obj['dataset']

    script = module_from_file(scriptname, ds.script_path)
    if script is None:
        raise SystemExit("Error loading script '{}'".format(scriptname))

    if len(grapheme_set) > 0:
        if len(logogram_set) > 0:
            raise click.UsageError("Only logograms or graphemes can be processed.")
        target = Target.GRAPH
        subset = grapheme_set
    elif len(logogram_set) > 0:
        target = Target.LOGO
        subset = logogram_set
    else:
        raise click.UsageError("Either logogram or grapheme sets must be chosen.")

    number = 0
    for a in ds.get_annotations(target, subset):
        number = number + 1
        updated = script.process(a, ds)
        if updated:
            a.save()

    click.echo("Ran '{}' on {} annotations".format(scriptname, number))
