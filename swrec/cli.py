import click
from swrec import extract_symbols, generate, yolo

cli = click.Group('swrec', {
    'extract_symbols': extract_symbols.extract_symbols,
    'generate': generate.generate,
    'make_yolo_files': yolo.make_yolo_files
    })
