# 2020-04-07 Antonio F. G. Sevilla <afgs@ucm.es>

from flask import Flask, request, send_from_directory, session, redirect, url_for
import hashlib
import json
import logging
import os
from pathlib import Path
from string import Template

from quevedo.annotation import Annotation, Target

os.environ['WERKZEUG_RUN_MAIN'] = 'true'
app = Flask(__name__, static_url_path='')
logging.getLogger('werkzeug').disabled = True

app_data = {}


def annotation_info(a: Annotation):
    title_tag = app_data['meta_tags'][0]
    anot = a.anot
    if a.target == Target.SYMB:
        tags = anot['tags']
        if len(tags) > 0:
            annotated = True
            title = tags[0]
        else:
            annotated = False
            title = '?'
    else:
        annotated = len(anot.get('symbols', [])),
        title = anot['meta'].get(title_tag, '')
    return {
        'id': a.id, 'annotated': annotated,
        'set': anot.get('set', 'none'),
        'title': title
    }


def get_transcription_info(dir, id):
    anot_file = app_data['data_dir'] / '{}/{}.json'.format(dir, id)
    anot = json.loads(anot_file.read_text())
    return {'dir': dir, 'id': str(id), **annotation_info(anot)}


def load_dataset(dataset, language):
    app_data['dataset'] = dataset
    app_data['lang'] = language
    app_data['meta_tags'] = dataset.config['meta_tags']
    resolved = dataset.path.resolve()
    app_data['path'] = resolved
    app_data['exp_list'] = [e.name for e in dataset.list_experiments() if
                            e.is_trained()]
    app_data['config'] = dataset.config['web']
    app.secret_key = app_data['config']['secret_key']


def run(host, port, path):
    app_data['mount_path'] = '/' + path + '/' if path != '' else '/'
    app.run(host=host, port=port)


# ------------ API ------------------

@app.route('/api/save/<dir>/<idx>', methods=["POST"])
def edit_post(dir, idx):
    anot_file = app_data['data_dir'] / '{}/{}.json'.format(dir, idx)
    anot = json.loads(anot_file.read_text())
    new_info = {**anot, **request.get_json()}
    tran = next(t for t in app_data['dirs'][dir]['tran_list']
                if t['id'] == idx)
    tran.update(annotation_info(new_info))
    anot_file.write_text(json.dumps(new_info))
    return 'OK'


@app.route('/api/new/<dir>', methods=["POST"])
def new_tran(dir):
    dir_data = app_data['dirs'][dir]
    idx = dir_data['last_id'] + 1
    dir_data['last_id'] = idx
    new_t = Annotation(app_data['data_dir'] / '{}/{}'.format(dir, idx))
    new_t.create_from(binary_data=request.data)
    dir_data['tran_list'].append(get_transcription_info(dir, idx)),
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
        'symbols': predict(img, experiment),
        'tag_index': experiment._tag_index
    }


@app.route('/api/login', methods=["POST"])
def do_login():
    data = request.get_json()
    try:
        user = app_data['config']['users'][data["user"]]
        password = hashlib.new("sha1", data["pass"].encode("utf8")).hexdigest()
        if password == user['password']:
            session['user'] = user
            return redirect(url_for('index'))
    except KeyError:
        pass
    return "Unauthorized", 403


# ----------------- WEB APP ----------------

html_template = Template((Path(__file__).parent /
                          'static/page.html').read_text())


@app.route('/login')
def login_page():
    if app_data['config']['public']:
        return redirect(url_for('index'))
    ds = app_data['dataset']
    return html_template.substitute(
        title=ds.config['title'],
        mount_path=app_data['mount_path'],
        page='login',
        data="{}"
    )


@app.route('/list/<target>/<dir>')
@app.route('/', defaults={'target': None, 'dir': None})
def index(target, dir):
    if (not app_data['config']['public'] and 
            session.get('user', None) is None):
        return redirect(url_for('login_page'))

    ds = app_data['dataset']
    data = {
        'title': ds.config['title'],
        'path': str(app_data['path']),
        'columns': ds.config['tag_schema'],
    }

    if dir is None:
        data['list'] = [{'name': d} for d in ds.list_real_subsets()]
        data['list2'] = [{'name': d} for d in ds.list_symbol_subsets()]
        data['description'] = ds.config['description']
    else:
        data['target'] = target
        data['dir_name'] = dir
        if target == 'real':
            data['list'] = sorted((annotation_info(an)
                                  for an in ds.get_real(dir)),
                                  key=lambda i: i['id'])
            readme = ds.path / target / dir / 'README.md'
        else: #  if target == 'symbols':
            data['list'] = sorted((annotation_info(an)
                                  for an in ds.get_symbols(dir)),
                                  key=lambda i: i['id'])
            readme = ds.path / target / dir / 'README.md'
        if readme.exists():
            data['description'] = readme.read_text()

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
        'meta_tags': app_data['meta_tags'],
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


@app.route('/img/<target>/<dir>/<filename>')
def send_image(target, dir, filename):
    return send_from_directory(app_data['path'] / target / dir, filename)
