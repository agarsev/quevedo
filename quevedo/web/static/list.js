// 2020-12-02 Antonio F. G. Sevilla <afgs@ucm.es>

import Text from '../i18n.js';

const html = htm.bind(preact.h);
const { useState, useRef } = preactHooks;

preact.render(html`<${App} ...${window.quevedo_data} />`, document.body);

function App ({ title, path, description, columns, dir_name, list }) {
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
        fetch(`api/new/${dir_name}`, {
            method: 'POST',
            body: file
        }).then(r => {
            if (r.ok) return r.json();
            else throw r;
        }).then(({ id }) => {
            window.location = `edit/${dir_name}/${id}`;
        }).catch(setError);
    };

    return html`
        <header>
            ${in_dir?html`<a href="">${title}</a> » ${dir_name}`:title}
            <span class="message_text">${message}</span>
        </header>
        <pre><b>(${path})</b></pre>
        <pre><b>${Text['columns']}: ${columns.join(', ')}</b></pre>
        <pre>${description}</pre>
        <${in_dir?TransList:DirList} list=${list} upload=${upload} />
    `;
}

function DirList ({ list }) {
    return html`<ul class="List">
        ${list.map(t => html`<${DirEntry} ...${t} />`)}
        <li class="extra-space"></li>
    </ul>`;
}

function DirEntry ({ name }) {
    return html`<li class="Entry DirEntry">
        <h2>${name}</h2>
        <a href="list/${name}">📂</a>
    </li>`;
}

function TransList ({ list, upload }) {
    return html`<ul class="List">
        <${UpEntry} />
        <${NewEntry} upload=${upload} />
        ${list.map(t => html`<${TransEntry} ...${t} />`)}
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
        <input ref=${inputRef} type="file" accept="image/*"
            onchange=${sendFile} style="display: none" />
    </li>`;
}

function TransEntry ({ dir, id, meanings, set, annotated }) {
    const edit_link = `edit/${dir}/${id}`;
    return html`<li class="Entry TransEntry">
        <h2>${meanings[0]} <span class="set">(${set})</span></h2>
        <img src="img/${dir}/${id}.png" onclick=${() => window.location=edit_link}/>
        <p>
            <a href="${edit_link}">📝</a>
            ${annotated>0?`✔️ (${annotated})`:null}
        </p>
    </li>`;
}
