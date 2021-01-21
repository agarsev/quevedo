# 2020-04-07 Antonio F. G. Sevilla <afgs@ucm.es>

from flask import Flask, request, send_from_directory
import json
import logging
import os
from pathlib import Path
from string import Template

from quevedo.transcription import Transcription

os.environ['WERKZEUG_RUN_MAIN'] = 'true'
app = Flask(__name__, static_url_path='')
logging.getLogger('werkzeug').disabled = True

app_data = {}


def annotation_info(anot):
    return {
        'annotated': len(anot.get('symbols', {})),
        'set': anot.get('set', 'none'),
        'notes': anot.get('notes', ''),
    }


def get_transcription_info(dir, id):
    anot_file = app_data['data_dir'] / '{}/{}.json'.format(dir, id)
    anot = json.loads(anot_file.read_text())
    return {'dir': dir, 'id': str(id), **annotation_info(anot)}


def load_dataset(dataset, language):
    app_data['dataset'] = dataset
    app_data['lang'] = language
    resolved = dataset.path.resolve()
    app_data['path'] = resolved
    data_dir = resolved / 'real'
    app_data['data_dir'] = data_dir
    app_data['exp_list'] = [e.name for e in dataset.list_experiments() if
                            e.is_trained()]
    app_data['dirs'] = {}
    for d in app_data['data_dir'].glob('*'):
        if not d.is_dir():
            continue
        name = str(d.stem)
        ids = sorted(int(trans.stem) for trans in
                     d.glob("*.png"))
        dir_data = {'last_id': ids[-1]}
        dir_data['trans_list'] = list(map(lambda id: get_transcription_info(name, id),
                                          ids))
        app_data['dirs'][name] = dir_data


def run(host, port, path):
    app_data['mount_path'] = '/' + path + '/' if path != '' else '/'
    app.run(host=host, port=port)


# ------------ API ------------------

@app.route('/api/save/<dir>/<idx>', methods=["POST"])
def edit_post(dir, idx):
    anot_file = app_data['data_dir'] / '{}/{}.json'.format(dir, idx)
    anot = json.loads(anot_file.read_text())
    new_info = {**anot, **request.get_json()}
    trans = next(t for t in app_data['dirs'][dir]['trans_list']
                 if t['id'] == idx)
    trans.update(annotation_info(new_info))
    anot_file.write_text(json.dumps(new_info))
    return 'OK'


@app.route('/api/new/<dir>', methods=["POST"])
def new_trans(dir):
    dir_data = app_data['dirs'][dir]
    idx = dir_data['last_id'] + 1
    dir_data['last_id'] = idx
    new_t = Transcription(app_data['data_dir'] / '{}/{}'.format(dir, idx))
    new_t.create_from(binary_data=request.data)
    dir_data['trans_list'].append(get_transcription_info(dir, idx)),
    return {'id': new_t.id}


predict = None  # Do not load neural network until requested
last_experiment = None


@app.route('/api/auto_annotate/<dir>/<idx>')
def get_auto_annotations(dir, idx):
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

    img = (app_data['data_dir'] / '{}/{}.png'.format(dir, idx)).resolve()
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
        'title': ds.config['title'],
        'path': str(app_data['path']),
        'description': ds.config['description'],
        'columns': ds.config['tag_schema'],
    }

    if dir is None:
        data['list'] = [{'name': k} for k in app_data['dirs'].keys()]
    else:
        data['dir_name'] = dir
        data['list'] = app_data['dirs'][dir]['trans_list']

    return html_template.substitute(
        title=ds.config['title'],
        mount_path=app_data['mount_path'],
        page='list',
        data=json.dumps(data))


@app.route('/edit/<dir>/<idx>')
def edit(dir, idx):
    ds = app_data['dataset']
    full_id = '{}/{}'.format(dir, idx)
    idn = int(idx)
    anot = json.loads((app_data['data_dir'] / (full_id + '.json')).read_text())
    last_id = app_data['dirs'][dir]['last_id']
    data = {
        'title': ds.config['title'],
        'id': {'dir': dir, 'num': idn, 'full': full_id},
        'annotation_help': ds.config['annotation_help'],
        'exp_list': app_data['exp_list'],
        'columns': ds.config['tag_schema'],
        'links': {
            'prev': '{}/{}'.format(dir, idn - 1 if idn > 1 else last_id),
            'next': '{}/{}'.format(dir, idn + 1 if idn < last_id else 1),
        },
        'anot': anot,
    }
    return html_template.substitute(
        title='{} - {}'.format(ds.config['title'], idx),
        mount_path=app_data['mount_path'],
        page='edit',
        data=json.dumps(data))


@app.route('/i18n.js')
def internationalization():
    return app.send_static_file('i18n/{}.js'.format(app_data['lang']))


@app.route('/img/<dir>/<filename>')
def send_image(dir, filename):
    return send_from_directory(app_data['data_dir'] / dir, filename)
