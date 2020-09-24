import { html, render } from 'https://unpkg.com/htm/preact/index.mjs?module'

let mount_path = '';

function Entry ({ id, meanings, set, annotated }) {
    return html`<li class="Entry">
        <h2>${meanings[0]} <span class="set">(${set})</span></h2>
        <img src="${mount_path}img/${id}.png" />
        <p>
            <a href="${mount_path}edit/${id}">📝</a>
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

function App ({ title, path, description, trans_list }) {
    return html`
        <h1>${title}</h1>
        <pre><b>(${path})</b></pre>
        <pre>${description}</pre>
        <${List} trans_list=${trans_list} />
    `;
}

fetch('/api/list').then(r => r.json()).then(data => {
    document.title = `${document.title}: ${data.title}`;
    mount_path = data.mount_path;
    render(html`<${App} ...${data} />`, document.body);
});
