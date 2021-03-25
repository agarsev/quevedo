// 2020-12-02 Antonio F. G. Sevilla <afgs@ucm.es>

import Text from '../i18n.js';

const MAX_ANNO_TITLE = 20;

const html = htm.bind(preact.h);
const { useState, useRef } = preactHooks;

preact.render(html`<${App} ...${window.quevedo_data} />`, document.body);

function App ({ title, path, description, columns, dir_name, target,
        list, list2 }) {
    const in_dir = dir_name !== undefined;

    const [ message, setMessage ] = useState('');
    const setError = resp => {
        if (resp.status < 500) {
            resp.text().then(e => setMessage(`${Text['error']}: ${e}`));
        } else {
            setMessage(`${Text['error']}: ${resp.statusText}`);
        }
    }
    const upload = file => {
        fetch(`api/new/${target}/${dir_name}`, {
            method: 'POST',
            body: file
        }).then(r => {
            if (r.ok) return r.json();
            else throw r;
        }).then(({ id }) => {
            window.location = `edit/${target}/${dir_name}/${id}`;
        }).catch(setError);
    };

    return html`
        <header>
            ${in_dir?html`<a href="">${title}</a> » ${target}/${dir_name}`:title}
            <span class="message_text">${message}</span>
        </header>
        <pre><b>(${path})</b></pre>
        <pre><b>${Text['columns']}: ${columns.join(', ')}</b></pre>
        <pre>${description}</pre>
        <${in_dir?AnnoList:DirList} list=${list} list2=${list2}
            upload=${upload} />
    `;
}

function DirList ({ list, list2 }) {
    return html`<>
        <h2>${Text['list_logo']}</h2>
        <ul class="List">
            ${list.map(t => html`<${DirEntry} target='logo' ...${t} />`)}
            <li class="extra-space"></li>
        </ul>
        <h2>${Text['list_graph']}</h2>
        <ul class="List">
            ${list2.map(t => html`<${DirEntry} target='graph' ...${t} />`)}
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

function AnnoList ({ list, upload }) {
    return html`<ul class="List">
        <${UpEntry} />
        <${NewEntry} upload=${upload} />
        ${list.map(t => html`<${AnnoEntry} ...${t} />`)}
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

function AnnoEntry ({ id, title, set, annotated }) {
    const { target, dir_name } = window.quevedo_data;
    const dir = `${target}/${dir_name}`;
    const edit_link = `edit/${dir}/${id}`;
    title = title.length > MAX_ANNO_TITLE?
        title.substring(0, MAX_ANNO_TITLE-1)+'…':
        title;
    return html`<li class="Entry LogoEntry">
        <h2>${title} <span class="set">(${set})</span></h2>
        <img src="img/${dir}/${id}.png" onclick=${() => window.location=edit_link}/>
        <p>
            <a href="${edit_link}">📝</a>
            ${annotated>0?`✔️ (${annotated})`:null}
        </p>
    </li>`;
}
