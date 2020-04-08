# 2020-04-07 Antonio F. G. Sevilla <afgs@ucm.es>

import click
from flask import Flask, render_template, send_from_directory, request
import json
import logging
import os
from pathlib import Path 
import yaml

os.environ['WERKZEUG_RUN_MAIN'] = 'true'
app = Flask(__name__, template_folder='.')
logging.getLogger('werkzeug').disabled = True

config = {}

def annotated_status (anot):
    return len(anot.get('symbols', {}))

def get_transcription_info (idx):
    anot_file = config['data_dir'] / '{}.json'.format(idx)
    anot = json.loads(anot_file.read_text())
    return { 'id': idx,
        'annotated': annotated_status(anot),
        'meanings': anot.get('meanings', [])
        }

def load_dataset (path):
    resolved = path.resolve();
    config['path'] = resolved;
    data_dir = resolved / 'real';
    config['data_dir'] = data_dir
    config['info'] = yaml.safe_load((resolved / 'info.yaml').read_text());
    ids = sorted(int(trans.stem) for trans in data_dir.glob("*.png"))
    config['last_id'] = ids[-1]
    config['trans'] = list(map(get_transcription_info, ids))

@app.route('/')
def list_page ():
    return render_template('list.html', **config)

@app.route('/img/<filename>')
def send_image (filename):
    return send_from_directory(config['data_dir'], filename)

@app.route('/edit/<idx>')
def edit_page (idx):
    idn = int(idx)
    anot_file = config['data_dir'] / '{}.json'.format(idx)
    anot = json.loads(anot_file.read_text())
    return render_template('edit.html', **{ 'id': idx,
        'prev_link': '/edit/{}'.format(idn-1 if idn>1 else config['last_id']),
        'next_link': '/edit/{}'.format(idn+1 if idn<config['last_id'] else 1),
        'info': config['info'], **anot })

@app.route('/edit/<idx>', methods=["POST"])
def edit_post (idx):
    anot_file = config['data_dir'] / '{}.json'.format(idx)
    anot = json.loads(anot_file.read_text())
    new_info = { **anot, **request.get_json() }
    trans = next(t for t in config['trans'] if t['id'] == int(idx))
    trans['annotated'] = annotated_status(new_info)
    anot_file.write_text(json.dumps(new_info))
    return 'OK'

@click.command()
@click.argument('dataset', type=click.Path(exists=True))
@click.option('-h','--host',default='localhost')
@click.option('-p','--port',default='5000')
def run_tagger(dataset, host, port):
    ''' Runs a tagger web application for tagging a dataset.

    The files in the `real` directory will be listed. For each, bounding boxes
    of symbols can be added, along with their class/name, and meanings for the
    whole transcription. The information will be saved along the real
    transcription with a `json` extension.
    '''

    click.echo("Loading dataset...")
    load_dataset(Path(dataset))
    click.echo("Starting tagger at http://{}:{}".format(host, port));
    app.run()

if __name__ == '__main__':
    run_tagger()
