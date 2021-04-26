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
@click.option('--graphemes', '-g', multiple=True,
              help="Process graphemes from these sets")
@click.option('--logograms', '-l', multiple=True,
              help="Process graphemes from these sets")
@click.pass_obj
def run_script(obj, scriptname, graphemes, logograms):
    '''Run a data processing script on dataset objects. The script should be in
    the 'scripts' directory of the dataset, and have a "process" method.'''

    ds: Dataset = obj['dataset']

    script = module_from_file(scriptname, ds.path / 'scripts')
    if script is None:
        raise SystemExit("Error loading script '{}'".format(scriptname))

    number = 0

    if len(graphemes) > 0:
        if len(logograms) > 0:
            raise SystemExit("Only logograms or graphemes can be processed.")

        for a in ds.get_annotations(Target.GRAPH, graphemes):
            number = number + 1
            script.process(a)
    elif len(logograms) > 0:
        for a in ds.get_annotations(Target.LOGO, logograms):
            number = number + 1
            script.process(a)

    else:
        raise SystemExit("Either logograms or graphemes must be provided.")

    click.echo("Ran '{}' on {} annotations".format(scriptname, number))
