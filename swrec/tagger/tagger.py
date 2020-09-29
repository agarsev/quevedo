# 2020-04-07 Antonio F. G. Sevilla <afgs@ucm.es>

from flask import Flask, send_from_directory, request
import json
import logging
import os

os.environ['WERKZEUG_RUN_MAIN'] = 'true'
app = Flask(__name__, static_url_path='')
logging.getLogger('werkzeug').disabled = True

app_data = {}


def annotated_status(anot):
    return len(anot.get('symbols', {}))


def get_transcription_info(idx):
    anot_file = app_data['data_dir'] / '{}.json'.format(idx)
    anot = json.loads(anot_file.read_text())
    return {
        'id': idx,
        'annotated': annotated_status(anot),
        'set': anot.get('set', 'none'),
        'meanings': anot.get('meanings', [])
    }


def load_dataset(dataset):
    app_data['dataset'] = dataset
    resolved = dataset.path.resolve()
    app_data['path'] = resolved
    data_dir = resolved / 'real'
    app_data['data_dir'] = data_dir
    ids = sorted(int(trans.stem) for trans in data_dir.glob("*.png"))
    app_data['last_id'] = ids[-1]
    app_data['trans_list'] = list(map(get_transcription_info, ids))


def run(host, port, path):
    app_data['mount_path'] = '/' + path + '/' if path != '' else '/'
    app.run(host=host, port=port)


# ------------ API ------------------

@app.route('/api/transcriptions')
def all_transcriptions():
    ds = app_data['dataset']
    return {
        'title': ds.info['title'],
        'mount_path': app_data['mount_path'],
        'path': str(app_data['path']),
        'description': ds.info['description'],
        'trans_list': app_data['trans_list'],
    }


@app.route('/api/transcriptions/<idx>', methods=["GET"])
def one_transcription(idx):
    idn = int(idx)
    anot_file = app_data['data_dir'] / '{}.json'.format(idx)
    anot = json.loads(anot_file.read_text())
    ds = app_data['dataset']
    return {
        'title': ds.info['title'],
        'annotation_help': ds.info['annotation_help'],
        'mount_path': app_data['mount_path'],
        'links': {
            'prev': idn - 1 if idn > 1 else app_data['last_id'],
            'next': idn + 1 if idn < app_data['last_id'] else 1,
        },
        'anot': anot,
    }


@app.route('/api/transcriptions/<idx>', methods=["POST"])
def edit_post(idx):
    anot_file = app_data['data_dir'] / '{}.json'.format(idx)
    anot = json.loads(anot_file.read_text())
    new_info = {**anot, **request.get_json()}
    trans = next(t for t in app_data['trans_list'] if t['id'] == int(idx))
    trans['annotated'] = annotated_status(new_info)
    anot_file.write_text(json.dumps(new_info))
    return 'OK'


predict = None  # Do not load neural network until requested


@app.route('/auto/<idx>')
def get_auto_annotations(idx):
    global predict
    if predict is None:
        from swrec.darknet.test import init_darknet, predict as true_predict
        init_darknet(app_data['dataset'])
        predict = true_predict

    img = (app_data['data_dir'] / '{}.png'.format(idx)).resolve()
    return {'symbols': predict(img)}


# ----------------- WEB APP ----------------

@app.route('/')
def index():
    return app.send_static_file('list.html')


@app.route('/img/<filename>')
def send_image(filename):
    return send_from_directory(app_data['data_dir'], filename)
