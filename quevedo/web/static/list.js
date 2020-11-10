import Text from './i18n.js';

const html = htm.bind(preact.h);

let mount_path = '';

function Entry ({ id, meanings, set, annotated }) {
    return html`<li class="Entry">
        <h2>${meanings[0]} <span class="set">(${set})</span></h2>
        <img src="${mount_path}img/${id}.png" />
        <p>
            <a href="${mount_path}edit.html#${id}">📝</a>
            ${annotated>0?`✔️ (${annotated})`:null}
        </p>
    </li>`;
}

function List ({ trans_list }) {
    return html`<ul class="List">
        ${trans_list.map(t => html`<${Entry} ...${t} />`)}
        <li class="extra-space"></li>
    </ul>`;
}

function App ({ title, path, description, trans_list, columns }) {
    return html`
        <h1>${title}</h1>
        <pre><b>(${path})</b></pre>
        <pre><b>${Text['columns']}: ${columns.join(', ')}</b></pre>
        <pre>${description}</pre>
        <${List} trans_list=${trans_list} />
    `;
}

fetch('api/transcriptions').then(r => r.json()).then(data => {
    document.title = `${document.title}: ${data.title}`;
    mount_path = data.mount_path;
    preact.render(html`<${App} ...${data} />`, document.body);
});
