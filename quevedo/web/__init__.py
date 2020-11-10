# 2020-11-10 Antonio F. G. Sevilla <afgs@ucm.es>

import click
from pathlib import Path

languages = [str(fn.stem) for fn in
             (Path(__file__).parent / 'static/i18n').glob('*.js')]


@click.command()
@click.pass_obj
@click.option('-h', '--host', default='localhost')
@click.option('-p', '--port', default='5000')
@click.option('-m', '--mount-path', default='', help="Mount path for the web application")
@click.option('--browser/--no-browser', default=True, help="Launch browser with the web app")
@click.option('-l', '--language', help="Language for the UI (default from config file)",
              type=click.Choice(languages, case_sensitive=False))
def launcher(obj, host, port, browser, mount_path, language):
    ''' Run a web application for managing and annotating the transcriptions in
    the dataset.
    '''
    from quevedo.web import app

    dataset = obj['dataset']
    click.echo("Loading dataset '{}'...".format(dataset.info['title']))

    if language is None:
        language = dataset.info.get('web', {}).get('lang', 'en')

    app.load_dataset(dataset, language)
    url = "http://{}:{}".format(host, port)

    click.echo("Starting app at {}".format(url))
    if browser:
        click.launch(url)

    app.run(host, port, mount_path)
