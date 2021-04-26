// 2020-12-02 Antonio F. G. Sevilla <afgs@ucm.es>

import Text from './i18n.js';
import { useChangeStack, useList } from './common_state.js';
import { LogogramEditor } from './logo.js';
import { GraphemeEditor } from './graph.js';

const html = htm.bind(preact.h);
const { useState, useRef } = preactHooks;


preact.render(html`<${App} ...${window.quevedo_data} />`, document.body);

function App ({ title, target, id, annotation_help, links, anot,
    columns, net_list, meta_tags }) {

    const changes = useChangeStack();

    const [ meta, _setMeta ] = useState(anot.meta);
    const setMeta = (k, v) => {
        changes.push(() => _setMeta(meta), `UPD_META_${k}`);
        _setMeta({ ...meta, [k]: v });
    };

    const is_logo = target == 'logograms';

    if (is_logo) {
        var graphemes = useList(anot.graphemes, changes)
    } else {
        var tags = useList(anot.tags, changes);
    }

    const [ message, setMessage ] = useState('');
    const setError = resp => {
        if (resp.status < 500) {
            resp.text().then(e => setMessage(`${Text['error']}: ${e}`));
        } else {
            setMessage(`${Text['error']}: ${resp.statusText}`);
        }
    }

    const saveChanges = () => {
        changes.setSaving();
        setMessage(Text['saving']);
        if (is_logo) {
            var body = { meta, graphemes: graphemes.list }
        } else {
            var body = { meta, tags: tags.list }
        }
        fetch(`api/save/${id.full}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body)
        }).then(r => {
            if (r.ok) {
                changes.setSaved();
                setMessage(Text['saved']);
            } else throw r;
        }).catch(setError);
    };

    const autoAnnotate = network => {
        if ((is_logo?graphemes:tags).list.length > 0 && 
            !confirm(Text['confirm_generate'])) {
            return;
        }
        fetch(`api/auto_annotate/${id.full}${network?`?network=${network}`:''}`)
        .then(r => {
            if (r.ok) {
                return r.json();
            } else throw r;
        }).then(data => {
            if (is_logo) {
                // sort graphemes left-to-right (roughly) and top-to-bottom (strict)
                data.graphemes.sort((a, b) => {
                    let left_a = a.box[0]-a.box[2]/2;
                    let left_b = b.box[0]-b.box[2]/2;
                    if (Math.abs(left_b-left_a)<0.09) {
                        let top_a = a.box[1]-a.box[3]/2;
                        let top_b = b.box[1]-b.box[3]/2;
                        return top_a - top_b;
                    } else return left_a - left_b;
                });
                graphemes.set(data.graphemes);
            } else {
                tags.set(data.tags);
            }
        }).catch(setError);
    };

    return html`
        <${Header} ...${{title, id, links, saveChanges,
            message, show_save: changes.dirty>0, autoAnnotate,
            net_list, changes }} />
        <${MetaEditor} ...${{meta_tags, meta, setMeta}} />
        ${is_logo?
            html`<${LogogramEditor} ...${{id, graphemes, columns}} />`
            :html`<${GraphemeEditor} ...${{id, tags, columns}} />`}
        <pre>${annotation_help}</pre>
    `;
}

function Header ({ title, id, links, saveChanges, message, show_save,
    net_list, autoAnnotate, changes }) {

    const net_select = useRef({ value: null });

    return html`<header>
        <a href="">${title}</a> » 
        <a href="list/${id.dir}">${id.dir}</a> » ${id.num}
        <a href="edit/${id.dir}/${links.prev}">⬅️</a>
        <a href="edit/${id.dir}/${links.next}" tabIndex=3 >➡️</a>
        ${changes.some?html`<button onclick=${changes.undo}>↩️</button>`:null}
        ${show_save?html`<button tabIndex=2
            onclick=${saveChanges} >💾</button>`:null}
        <span class="message_text">${message}</span>
        ${net_list.length<1?null:html`<select ref=${net_select}>
            ${net_list.map(e=>html`<option value=${e}>${e}</option>`)}
        </select>`}
        <button onclick=${() => autoAnnotate(net_select.current.value)}>⚙️</button>
    </header>`;
}

function MetaEditor ({ meta_tags, meta, setMeta }) {
    return html`<div class="MetaEditor">
        <h2>${Text['meta']}</h2>
        <table>${meta_tags.map(k => html`<tr>
            <th>${k}:</th>
            <td><textarea rows="1" autocomplete="off"
                oninput=${e => setMeta(k, e.target.value)}
                value=${meta[k] || ''} />
            </td>
        </tr>`)}</table>
    </div>`;
}
