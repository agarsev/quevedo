# 2020-11-10 Antonio F. G. Sevilla <afgs@ucm.es>
# Licensed under the Open Software License version 3.0

import click
from pathlib import Path

languages = [str(fn.stem) for fn in
             (Path(__file__).parent / 'static/i18n').glob('*.js')]


@click.command('web')
@click.pass_obj
@click.option('-h', '--host')
@click.option('-p', '--port')
@click.option('-m', '--mount-path', help="Mount path for the web application")
@click.option('--browser/--no-browser', default=True, help="Launch browser with the web app")
@click.option('-l', '--language', help="Language for the UI (default from config file)",
              type=click.Choice(languages, case_sensitive=False))
def launcher(obj, host, port, browser, mount_path, language):
    '''Run a web interface to the dataset.

    The web application launched can be used to browse and manage the
    dataset files. Annotation pages are provided for both graphemes and
    logograms to allow visual annotation of objects. Very basic user management
    is also provided. Configuration can be written under the `web` key of the
    dataset configuration.'''
    from quevedo.web import app

    dataset = obj['dataset']
    click.echo("Loading dataset '{}'...".format(dataset.config['title']))

    config = dataset.config.get('web', {})
    if language is None:
        language = config.get('lang', 'en')
    if host is None:
        host = config.get('host', 'localhost')
    if port is None:
        port = config.get('port', '5000')
    if mount_path is None:
        mount_path = config.get('mount_path', '')

    app.load_dataset(dataset, language)
    url = "http://{}:{}".format(host, port)

    click.echo("Starting app at {}".format(url))
    if browser:
        click.launch(url)

    app.run(host, port, mount_path)
