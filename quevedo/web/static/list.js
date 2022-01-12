// 2020-12-02 Antonio F. G. Sevilla <afgs@ucm.es>
// Licensed under the Open Software License version 3.0

import Text from './i18n.js';
import { useSavedState } from './common_state.js';

const MAX_ANNO_TITLE = 20;

const html = htm.bind(preact.h);
const { useState, useRef } = preactHooks;

preact.render(html`<${App} ...${window.quevedo_data} />`, document.body);

function App ({ title, path, description, dir_name, target,
        list, list2, flags }) {
    const in_dir = dir_name !== undefined;

    const [ message, setMessage ] = useState('');
    const setError = resp => {
        if (resp.status < 500) {
            resp.text().then(e => setMessage(`${Text['error']}: ${e}`));
        } else {
            setMessage(`${Text['error']}: ${resp.statusText}`);
        }
    }
    const upload = in_dir ? file => {
        fetch(`api/new/${target}/${dir_name}`, {
            method: 'POST',
            body: file
        }).then(r => {
            if (r.ok) return r.json();
            else throw r;
        }).then(({ id }) => {
            window.location = `edit/${target}/${dir_name}/${id}`;
        }).catch(setError);
    } : (target, dir_name) => {
        fetch(`api/new/${target}/${dir_name}`)
            .then(() => window.location = `list/${target}/${dir_name}`)
            .catch(setError);
    };

    const [ filter, setFilter ] = useSavedState('filter', {});
    const [ _filterMode, setFilterMode ] = useSavedState('filterMode', 'any');
    const search = Object.keys(filter).filter(f => filter[f] == true);
    let view = list;
    let filterMode = '';
    if (in_dir && search.length>0) {
        filterMode = _filterMode;
        if (_filterMode === 'any') {
            view = list.filter(t => search.some(s => t.flags.includes(s)));
        } else if (_filterMode === 'all') {
            view = list.filter(t => search.every(s => t.flags.includes(s)));
        } else if (_filterMode === 'none') {
            view = list.filter(t => search.every(s => !t.flags.includes(s)));
        }
    }

    return html`
        <header>
            ${in_dir?html`<a href="">${title}</a> » ${target}/${dir_name}`:title}
            <span class="message_text">${message}</span>
        </header>
        <pre><b>(${path})</b></pre>
        <pre>${description}</pre>
        ${in_dir?html`<${Filter} ...${{ flags, filter, setFilter, filterMode,
            setFilterMode }} />`:null}
        <${in_dir?AnnoList:DirList} list=${view} list2=${list2}
            upload=${filterMode===''?upload:null} />
    `;
}

function Filter ({ flags, filter, setFilter, filterMode, setFilterMode }) {
    return html`<form class="Filter">
        ${Text['quick_filter']}: ${Object.keys(flags).map(f => {
            const icon = flags[f];
            return html`<label class="flag_icon">
                <input type="checkbox" name=${f} checked=${filter[icon]?true:false}
                    onChange=${e => setFilter({ ...filter, [icon]: e.target.checked })} />
                ${icon}</label>`;
        })}
        <label><input type="radio" name="filterMode" value="any"
            checked=${filterMode === 'any'} onChange=${e => setFilterMode('any')} />
            ${Text['any']}</label>
        <label><input type="radio" name="filterMode" value="all"
            checked=${filterMode === 'all'} onChange=${e => setFilterMode('all')} />
            ${Text['all']}</label>
        <label><input type="radio" name="filterMode" value="none"
            checked=${filterMode === 'none'} onChange=${e => setFilterMode('none')} />
            ${Text['none']}</label>
    </form>`;
}


function DirList ({ list, list2, upload }) {
    return html`<>
        <h2>${Text['list_logo']}</h2>
        <ul class="List">
            ${list.map(t => html`<${DirEntry} target='logograms' ...${t} />`)}
            ${upload?html`
                <${NewDir} upload=${dirname => upload('logograms', dirname)} />
            `:null}
            <li class="extra-space"></li>
        </ul>
        <h2>${Text['list_graph']}</h2>
        <ul class="List">
            ${list2.map(t => html`<${DirEntry} target='graphemes' ...${t} />`)}
            ${upload?html`
                <${NewDir} upload=${dirname => upload('graphemes', dirname)} />
            `:null}
            <li class="extra-space"></li>
        </ul>
    `;
}

function DirEntry ({ name, count, target }) {
    return html`<li class="Entry DirEntry">
        <h2>${name} <span class="set">(${count})</span></h2>
        <a href="list/${target}/${name}">📂</a>
    </li>`;
}

function NewDir ({ upload }) {
    let new_dir = () => {
        let name = prompt(Text['name_for_subset']);
        if (name) upload(name);
    };
    return html`<li class="Entry DirEntry">
        <h2>${Text['new_subset']}</h2>
        <a href="#" onclick=${new_dir}>📤</a>
    </li>`;
}

function AnnoList ({ list, upload }) {
    return html`<ul class="List">
        <${UpEntry} />
        ${list.map(t => html`<${AnnoEntry} ...${t} />`)}
        ${upload?html`<${NewEntry} upload=${upload} />`:null}
        <li class="extra-space"></li>
    </ul>`;
}

function UpEntry () {
    return html`<li class="Entry DirEntry">
        <h2>${Text['back']}</h2>
        <a href="">📂</a>
    </li>`;
}

function NewEntry ({ upload }) {
    const inputRef = useRef(null);
    const clickLink = e => {
        inputRef.current.click();
        e.preventDefault();
    };
    const sendFile = () => {
        const ip = inputRef.current;
        if (ip.files.length>0) {
            upload(ip.files[0]);
        }
    };
    return html`<li class="Entry DirEntry">
        <h2>${Text['new_entry']}</h2>
        <a href="#" onclick=${clickLink}>📤</a>
        <input ref=${inputRef} type="file" accept=".png"
            onchange=${sendFile} style="display: none" />
    </li>`;
}

function AnnoEntry ({ id, title, set, flags }) {
    const { target, dir_name } = window.quevedo_data;
    const dir = `${target}/${dir_name}`;
    const edit_link = `edit/${dir}/${id}`;
    title = title.length > MAX_ANNO_TITLE?
        title.substring(0, MAX_ANNO_TITLE-1)+'…':
        title;
    return html`<li class="Entry LogoEntry">
        <h2>${id} — ${title}</h2>
        <a href="${edit_link}">
            <img src="img/${dir}/${id}.png" />
        </a>
        <p>
            ${flags.map(f => html`<span class="flag">${f}</span>`)}
            <span class="set">(${set})</span>
        </p>
    </li>`;
}
