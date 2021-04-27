# 2021-04-26 Antonio F. G. Sevilla <afgs@ucm.es>

import click
import importlib.util

from quevedo import Dataset, Target


# From @wecsam
# https://stackoverflow.com/questions/4383571/importing-files-from-different-folder
def module_from_file(module_name, file_path):
    file = (file_path / module_name).with_suffix('.py')
    spec = importlib.util.spec_from_file_location(module_name, file)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@click.command()
@click.option('--scriptname', '-s', required=True,
              help="Name of the script to run")
@click.option('--grapheme-set', '-g', multiple=True,
              help="Process graphemes from these sets")
@click.option('--logogram-set', '-l', multiple=True,
              help="Process graphemes from these sets")
@click.pass_obj
def run_script(obj, scriptname, grapheme_set, logogram_set):
    '''Run a data processing script on dataset objects. The script should be in
    the 'scripts' directory of the dataset, and have a "process" method.'''

    ds: Dataset = obj['dataset']

    script = module_from_file(scriptname, ds.path / 'scripts')
    if script is None:
        raise SystemExit("Error loading script '{}'".format(scriptname))

    number = 0

    if len(grapheme_set) > 0:
        if len(logogram_set) > 0:
            raise click.UsageError("Only logograms or graphemes can be processed.")

        for a in ds.get_annotations(Target.GRAPH, grapheme_set):
            number = number + 1
            script.process(a)
    elif len(logogram_set) > 0:
        for a in ds.get_annotations(Target.LOGO, logogram_set):
            number = number + 1
            script.process(a)
    else:
        raise click.UsageError("Either logogram or grapheme sets must be chosen.")

    click.echo("Ran '{}' on {} annotations".format(scriptname, number))
