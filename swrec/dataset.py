# 2020-04-09 Antonio F. G. Sevilla <afgs@ucm.es>

import click
from pathlib import Path
import yaml

class Dataset:

    def __init__ (self, path):
        self.path = Path(path)


def style (condition, right, wrong=None):
    color = "green" if condition else "red"
    text = right if (condition or (wrong is None)) else wrong
    return click.style(str(text), fg=color)

@click.command()
@click.pass_obj
def info (dataset):
    ''' Returns status information about a dataset.'''
    path = dataset.path
    info = yaml.safe_load((path / 'info.yaml').read_text())
    click.secho('{}\n=====\n'.format(info["title"]), bold=True)
    click.echo(info["description"])

    num_real = sum(1 for _ in (path / 'real').glob('*.png'))
    click.echo('Real transcriptions: {}'.format(style(True, num_real)))
    num_annot = sum(1 for _ in (path / 'real').glob('*.json'))
    click.echo('Annotated: {}/{}\n'.format(style(num_annot==num_real, num_annot),
        num_real))

    symbols = path / 'symbols'
    num_sym = sum(1 for _ in symbols.glob('*.png'))
    click.echo('Symbols extracted: {}'.format(style(symbols.exists(), num_sym, 'no')))

    gen = path / 'generated'
    num_gen = sum(1 for _ in gen.glob('*.png'))
    click.echo('Transcriptions generated: {}\n'.format(style(gen.exists(), num_gen, 'no')))
