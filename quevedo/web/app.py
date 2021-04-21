# 2020-04-07 Antonio F. G. Sevilla <afgs@ucm.es>
# vi:foldmethod=marker

from flask import Flask, request, send_from_directory, session, redirect, url_for
from functools import wraps
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

# {{{ ---- Dataset loading and utils


def string_to_target(t):
    return Target.LOGO if t == 'logograms' else Target.GRAPH


def annotation_info(a: Annotation):
    title_tag = app_data['meta_tags'][0]
    anot = a.anot
    if a.target == Target.GRAPH:
        tags = anot['tags']
        if len(tags) > 0:
            annotated = True
            title = tags[0]
        else:
            annotated = False
            title = '?'
    else:
        annotated = len(anot.get('graphemes', [])),
        title = anot['meta'].get(title_tag, '')
    return {
        'id': a.id, 'annotated': annotated,
        'set': anot.get('set', 'none'),
        'title': title
    }


def get_annotation_info(dir, id):
    anot_file = app_data['data_dir'] / '{}/{}.json'.format(dir, id)
    anot = json.loads(anot_file.read_text())
    return {'dir': dir, 'id': str(id), **annotation_info(anot)}


def load_dataset(dataset, language):
    app_data['dataset'] = dataset
    app_data['lang'] = language
    app_data['meta_tags'] = dataset.config['meta_tags']
    resolved = dataset.path.resolve()
    app_data['path'] = resolved
    app_data['net_list'] = [n.name for n in dataset.list_networks() if
                            n.is_trained()]
    app_data['config'] = dataset.config['web']
    app.secret_key = app_data['config']['secret_key']


def run(host, port, path):
    app_data['mount_path'] = '/' + path + '/' if path != '' else '/'
    app.run(host=host, port=port)


# }}}
# {{{ ---- AUTH

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


def authenticated(func):
    @wraps(func)
    def check_auth(*args, **kwargs):
        if (not app_data['config']['public'] and
                session.get('user', None) is None):
            return redirect(url_for('login_page'))
        return func(*args, **kwargs)
    return check_auth


# }}}
# {{{ ---- API

@app.route('/api/save/<target>/<dir>/<idx>', methods=["POST"])
@authenticated
def edit_post(target, dir, idx):
    ds = app_data['dataset']
    single = ds.get_single(string_to_target(target), dir, idx)
    single.anot.update(request.get_json())
    single.save()
    return 'OK'


@app.route('/api/new/<target>/<dir>', methods=["POST"])
@authenticated
def new_annotation(target, dir):
    ds = app_data['dataset']
    new_t = ds.new_single(string_to_target(target), dir)
    new_t.create_from(binary_data=request.data)
    return {'id': new_t.id}


@app.route('/api/predict/<target>/<dir>/<idx>')
@authenticated
def get_predict(target, dir, idx):
    ds = app_data['dataset']
    network = ds.get_network(request.args.get('network', None))

    an = ds.get_single(string_to_target(target), dir, idx)
    return {
        'graphemes': network.predict(an.image),
        'tag_index': network._tag_index
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


# }}}
# {{{ ---- WEB APP

html_template = Template((Path(__file__).parent /
                          'static/page.html').read_text())


@app.route('/list/<target>/<dir>')
@app.route('/', defaults={'target': None, 'dir': None})
@authenticated
def index(target, dir):
    ds = app_data['dataset']
    data = {
        'title': ds.config['title'],
        'path': str(app_data['path']),
        'columns': ds.config['tag_schema'],
    }

    if dir is None:
        data['list'] = ds.get_subsets(Target.LOGO)
        data['list2'] = ds.get_subsets(Target.GRAPH)
        data['description'] = ds.config['description']
    else:
        data['target'] = target
        data['dir_name'] = dir
        annots = ds.get_annotations(string_to_target(target), dir)
        data['list'] = sorted((annotation_info(an)
                              for an in annots),
                              key=lambda i: int(i['id']))
        readme = ds.path / target / dir / 'README.md'
        if readme.exists():
            data['description'] = readme.read_text()

    return html_template.substitute(
        title=ds.config['title'],
        mount_path=app_data['mount_path'],
        page='list',
        data=json.dumps(data))


@app.route('/edit/<target>/<dir>/<idx>')
@authenticated
def edit(target, dir, idx):
    ds = app_data['dataset']
    full_dir = '{}/{}'.format(target, dir)
    full_id = '{}/{}/{}'.format(target, dir, idx)
    idn = int(idx)

    if idn > 1:
        prev_link = idn - 1
    else:
        prev_link = sum(1 for _ in (ds.path / full_dir).glob('*.png'))

    next_link = idn + 1
    if not (ds.path / full_dir / str(next_link)).with_suffix('.png').exists():
        next_link = 1

    a = ds.get_single(string_to_target(target), dir, idx)

    data = {
        'title': ds.config['title'],
        'target': target,
        'id': {
            'dir': full_dir,
            'num': idn,
            'full': full_id
        },
        'links': {
            'prev': prev_link,
            'next': next_link,
        },
        'annotation_help': ds.config['annotation_help'],
        'net_list': app_data['net_list'],
        'meta_tags': app_data['meta_tags'],
        'columns': ds.config['tag_schema'],
        'anot': a.anot,
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


@app.route('/quevedo_logo.png')
def favicon():
    return send_from_directory(Path(__file__).parent.parent.resolve(), 'logo_icon.png')

# }}}
