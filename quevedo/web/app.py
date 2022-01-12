# 2020-04-07 Antonio F. G. Sevilla <afgs@ucm.es>
# Licensed under the Open Software License version 3.0
# vi:foldmethod=marker

from flask import Flask, request, send_from_directory, session, redirect
from functools import wraps
import hashlib
from itertools import chain
import json
import logging
import os
from pathlib import Path
import re
from string import Template

from quevedo.annotation import Annotation, Target
from quevedo.run_script import module_from_file

os.environ['WERKZEUG_RUN_MAIN'] = 'true'
app = Flask(__name__, static_url_path='')
logging.getLogger('werkzeug').disabled = True

app_data = {}

# {{{ ---- Dataset loading and utils


def string_to_target(t):
    return Target.LOGO if t == 'logograms' else Target.GRAPH


def annotation_info(a: Annotation):
    title_tag = app_data['meta_tags'][0]
    title = a.meta.get(title_tag, '')
    flags = app_data['flags']
    flag_icons = [icon for f, icon in flags.items()
                  if a.meta.get(f, False)]
    return {
        'id': a.id, 'flags': flag_icons,
        'set': a.fold, 'title': title
    }


DEFAULT_COLOR_LIST = ['#FF0000', '#00FF00', '#0000FF', '#FF00FF', '#00FFFF',
                      '#880000', '#008800', '#000088', '#888800', '#008888']


def load_dataset(dataset, language):
    app_data['dataset'] = dataset
    app_data['lang'] = language
    app_data['meta_tags'] = dataset.config['meta_tags']
    app_data['flags'] = dataset.config['flags']
    resolved = dataset.path.resolve()
    app_data['path'] = resolved
    app_data['config'] = dataset.config['web']
    app.secret_key = app_data['config']['secret_key']
    app_data['nets'] = {
        'graphemes': {n.name: None for n in dataset.list_networks() if
                      n.target == Target.GRAPH and n.is_trained()},
        'logograms': {n.name: None for n in dataset.list_networks() if
                      n.target == Target.LOGO and n.is_trained()},
    }
    app_data['scripts'] = {
        'graphemes': {'_'.join(s.stem.split('_')[1:]): None
                      for s in dataset.script_path.glob('*.py')
                      if s.stem.startswith('graph')},
        'logograms': {'_'.join(s.stem.split('_')[1:]): None
                      for s in dataset.script_path.glob('*.py') 
                      if s.stem.startswith('logo')}
    }
    app_data['pipes'] = {
        'graphemes': {n.name: None for n in dataset.list_pipelines() if
                      n.target == Target.GRAPH},
        'logograms': {n.name: None for n in dataset.list_pipelines() if
                      n.target == Target.LOGO},
    }
    app_data['color_list'] = dataset.config['web'].get('colors', DEFAULT_COLOR_LIST)


def run(host, port, path):
    app_data['mount_path'] = '/' + path + '/' if path != '' else '/'
    app.run(host=host, port=port)


# }}}
# {{{ ---- AUTH

@app.route('/login')
def login_page():
    if (app_data['config']['public'] or
            session.get('user', None) is not None):
        return redirect(app_data['mount_path'])
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
            return redirect(app_data['mount_path'] + 'login')
        return func(*args, **kwargs)
    return check_auth


def can_do(path, action, compiled_action):
    u = session.get('user')
    if u is None:
        return True
    try:
        perms = u[compiled_action]
    except KeyError:
        perms = u.get(action, [])
        if len(perms) == 0:
            perms = 'NONE'
        elif perms != 'ALL' and perms != 'NONE':
            perms = [re.compile(r) for r in perms]
        u[compiled_action] = perms
    if perms == 'ALL':
        return True
    if perms == 'NONE':
        return False
    for p in perms:
        if p.search(path):
            return True
    return False


def can_write(target, dir):
    return can_do('{}/{}'.format(target, dir), 'write', 'write_')


def can_read(target, dir):
    return can_do('{}/{}'.format(target, dir), 'read', 'read_')


# }}}
# {{{ ---- API

@app.route('/api/save/<target>/<dir>/<idx>', methods=["POST"])
@authenticated
def edit_post(target, dir, idx):
    if not can_write(target, dir):
        return "Unauthorized", 403
    ds = app_data['dataset']
    single = ds.get_single(string_to_target(target), dir, idx)
    single.update(**request.get_json())
    single.save()
    return 'OK'


@app.route('/api/new/<target>/<dir>', methods=["POST"])
@authenticated
def new_annotation(target, dir):
    if not can_write(target, dir):
        return "Unauthorized", 403
    ds = app_data['dataset']
    new_t = ds.new_single(string_to_target(target), dir,
                          binary_data=request.data)
    return {'id': new_t.id}


@app.route('/api/new/<target>/<dir>', methods=["GET"])
@authenticated
def new_dir(target, dir):
    if not can_write(target, dir):
        return "Unauthorized", 403
    ds = app_data['dataset']
    ds.create_subset(string_to_target(target), dir)
    return 'OK'


@app.route('/api/run/<function>/<target>/<dir>/<idx>')
@authenticated
def run_backend(function, target, dir, idx):
    ds = app_data['dataset']
    an = ds.get_single(string_to_target(target), dir, idx)
    if function in app_data['nets'][target]:
        net = app_data['nets'][target][function]
        if net is None:
            net = ds.get_network(function)
            app_data['nets'][target][function] = net
        net.auto_annotate(an)
    elif function in app_data['scripts'][target]:
        script = app_data['scripts'][target][function]
        if script is None:
            script = module_from_file(target[:-1]+'_'+function, ds.script_path)
            try:
                script.init(ds, web=True)
            except AttributeError:
                pass
            app_data['scripts'][target][function] = script
        script.process(an, ds)
    elif function in app_data['pipes'][target]:
        pipe = app_data['pipes'][target][function]
        if pipe is None:
            pipe = ds.get_pipeline(function)
            app_data['pipes'][target][function] = pipe
        pipe.run(an)
    else:
        return "Unknown network, pipeline or script '{}'".format(function), 404
    return an.to_dict()


@app.route('/api/login', methods=["POST"])
def do_login():
    data = request.get_json()
    try:
        user = app_data['config']['users'][data["user"]]
        password = hashlib.new("sha1", data["pass"].encode("utf8")).hexdigest()
        if password == user['password']:
            session['user'] = user
            return redirect(app_data['mount_path'])
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
        'g_tags': ds.config['g_tags'],
        'l_tags': ds.config['l_tags'],
        'e_tags': ds.config['e_tags'],
        'meta_tags': ds.config['meta_tags'],
        'flags': ds.config['flags'],
    }

    if dir is None:
        data['list'] = list(filter(lambda d: can_read('logograms', d['name']),
                                   ds.get_subsets(Target.LOGO)))

        data['list2'] = list(filter(lambda d: can_read('graphemes', d['name']),
                                    ds.get_subsets(Target.GRAPH)))
        data['description'] = ds.config['description']
    elif not can_read(target, dir):
        return "Unauthorized", 403
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
    if not can_read(target, dir):
        return "Unauthorized", 403
    ds = app_data['dataset']
    full_dir = '{}/{}'.format(target, dir)
    full_id = '{}/{}/{}'.format(target, dir, idx)
    target_ = string_to_target(target)
    idn = int(idx)

    if idn > 1:
        prev_link = idn - 1
    else:
        prev_link = sum(1 for _ in (ds.path / full_dir).glob('*.png'))

    next_link = idn + 1
    if not (ds.path / full_dir / str(next_link)).with_suffix('.png').exists():
        next_link = 1

    a = ds.get_single(target_, dir, idx)
    functions = [f for f in chain(app_data['nets'][target].keys(),
                                  app_data['pipes'][target].keys(),
                                  app_data['scripts'][target].keys())]

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
        'functions': functions,
        'meta_tags': app_data['meta_tags'],
        'flags': app_data['flags'],
        'g_tags': ds.config['g_tags'],
        'l_tags': ds.config['l_tags'],
        'e_tags': ds.config['e_tags'],
        'meta_tags': ds.config['meta_tags'],
        'color_list': app_data['color_list'],
        'anot': a.to_dict(),
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
