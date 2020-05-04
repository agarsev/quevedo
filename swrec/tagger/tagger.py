# 2020-04-07 Antonio F. G. Sevilla <afgs@ucm.es>

from flask import Flask, render_template, send_from_directory, request
import json
import logging
import os

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

def load_dataset (dataset):
    config['dataset'] = dataset
    resolved = dataset.path.resolve();
    config['path'] = resolved;
    data_dir = resolved / 'real';
    config['data_dir'] = data_dir
    config['info'] = dataset.info
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
        'mount': config['mount'],
        'prev_link': 'edit/{}'.format(idn-1 if idn>1 else config['last_id']),
        'next_link': 'edit/{}'.format(idn+1 if idn<config['last_id'] else 1),
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

predict = None
@app.route('/auto/<idx>')
def get_auto_annotations (idx):
    global predict
    if predict is None:
        from swrec.darknet.test import init_darknet, predict as true_predict
        init_darknet(config['dataset'])
        predict = true_predict

    img = (config['data_dir'] / '{}.png'.format(idx)).resolve()
    return { 'symbols': predict(img) }

def run (host, port, path):
    config['mount'] = '/'+path+'/' if path != '' else '/'
    app.run(host=host, port=port)
