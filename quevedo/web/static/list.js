import Text from '../i18n.js';

const html = htm.bind(preact.h);

preact.render(html`<${App} ...${window.quevedo_data} />`, document.body);

function App ({ title, path, description, columns, dir_name, list }) {
    const in_dir = dir_name !== undefined;
    return html`
        <header>
            ${in_dir?html`<a href="">${title}</a> » ${dir_name}`:title}
        </header>
        <pre><b>(${path})</b></pre>
        <pre><b>${Text['columns']}: ${columns.join(', ')}</b></pre>
        <pre>${description}</pre>
        <${List} list=${list} in_dir=${in_dir} />
    `;
}

function List ({ list, in_dir }) {
    const Entry = in_dir?TransEntry:DirEntry;
    return html`<ul class="List">
        ${in_dir?html`<${UpEntry} />`:null}
        ${list.map(t => html`<${Entry} ...${t} />`)}
        <li class="extra-space"></li>
    </ul>`;
}

function DirEntry ({ name }) {
    return html`<li class="Entry DirEntry">
        <h2>${name}</h2>
        <a href="list/${name}">📂</main>
    </li>`;
}

function UpEntry () {
    return html`<li class="Entry DirEntry">
        <h2>${Text['back']}</h2>
        <a href="">📂</main>
    </li>`;
}

function TransEntry ({ id, meanings, set, annotated }) {
    const edit_link = `edit/${id}`;
    return html`<li class="Entry TransEntry">
        <h2>${meanings[0]} <span class="set">(${set})</span></h2>
        <img src="img/${id}.png" onclick=${() => window.location=edit_link}/>
        <p>
            <a href="${edit_link}">📝</a>
            ${annotated>0?`✔️ (${annotated})`:null}
        </p>
    </li>`;
}
