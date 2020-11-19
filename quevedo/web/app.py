# 2020-04-07 Antonio F. G. Sevilla <afgs@ucm.es>

from flask import Flask, send_from_directory, request
import json
import logging
import os
from pathlib import Path
from string import Template

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


def load_dataset(dataset, language):
    app_data['dataset'] = dataset
    app_data['lang'] = language
    resolved = dataset.path.resolve()
    app_data['path'] = resolved
    data_dir = resolved / 'real'
    app_data['data_dir'] = data_dir
    app_data['exp_list'] = dataset.list_experiments()
    app_data['dirs'] = {}
    for d in app_data['data_dir'].glob('*'):
        if not d.is_dir():
            continue
        name = str(d.stem)
        ids = sorted(int(trans.stem) for trans in
                     d.glob("*.png"))
        dir_data = {'last_id': ids[-1]}
        ids = ('{}/{}'.format(name, t) for t in ids)
        dir_data['trans_list'] = list(map(get_transcription_info, ids))
        app_data['dirs'][name] = dir_data


def run(host, port, path):
    app_data['mount_path'] = '/' + path + '/' if path != '' else '/'
    app.run(host=host, port=port)


# ------------ API ------------------

@app.route('/api/transcriptions/<idx>', methods=["GET"])
def one_transcription(idx):
    idn = int(idx)
    anot_file = app_data['data_dir'] / '{}.json'.format(idx)
    anot = json.loads(anot_file.read_text())
    ds = app_data['dataset']
    return {
        'title': ds.info['title'],
        'annotation_help': ds.info['annotation_help'],
        'exp_list': app_data['exp_list'],
        'mount_path': app_data['mount_path'],
        'columns': ds.info['tag_schema'],
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
last_experiment = None


@app.route('/api/auto_annotate/<idx>')
def get_auto_annotations(idx):
    ds = app_data['dataset']
    experiment = ds.get_experiment(request.args.get('exp', None))

    global predict, last_experiment
    if predict is None or last_experiment.name != experiment.name:
        from quevedo.darknet.predict import init_darknet, predict as true_predict
        try:
            init_darknet(ds, experiment)
            predict = true_predict
            last_experiment = experiment
        except SystemExit as e:
            return str(e), 400

    img = (app_data['data_dir'] / '{}.png'.format(idx)).resolve()
    return {
        'symbols': predict(img),
        'tag_index': experiment._tag_index
    }


# ----------------- WEB APP ----------------

html_template = Template((Path(__file__).parent /
                          'static/page.html').read_text())


@app.route('/list/<dir>')
@app.route('/', defaults={'dir': None})
def index(dir):
    ds = app_data['dataset']
    data = {
        'title': ds.info['title'],
        'path': str(app_data['path']),
        'description': ds.info['description'],
        'columns': ds.info['tag_schema'],
    }

    if dir is None:
        data['list'] = [{'name': k} for k in app_data['dirs'].keys()]
    else:
        data['dir_name'] = dir
        data['list'] = app_data['dirs'][dir]['trans_list']

    return html_template.substitute(
        title=ds.info['title'],
        mount_path=app_data['mount_path'],
        page='list',
        data=json.dumps(data))


@app.route('/i18n.js')
def internationalization():
    return app.send_static_file('i18n/{}.js'.format(app_data['lang']))


@app.route('/img/<dir>/<filename>')
def send_image(dir, filename):
    return send_from_directory(app_data['data_dir'] / dir, filename)
