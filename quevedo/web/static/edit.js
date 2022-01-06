// 2020-12-02 Antonio F. G. Sevilla <afgs@ucm.es>
// Licensed under the Open Software License version 3.0

import Text from './i18n.js';
import { useChangeStack, useList, useDict, useSavedState } from './common_state.js';
import { LogogramEditor } from './logo.js';
import { GraphemeEditor } from './graph.js';

const html = htm.bind(preact.h);
const { useState } = preactHooks;


preact.render(html`<${App} ...${window.quevedo_data} />`, document.body);

function App ({ title, target, id, annotation_help, links, anot,
    functions, g_tags, l_tags, e_tags, meta_tags, flags, color_list }) {

    const changes = useChangeStack();
    const meta = useDict(anot.meta, changes);
    const is_logo = target == 'logograms';

    const graphemes = is_logo?useList(anot.graphemes, changes):null;
    const edges = is_logo?useList(anot.edges, changes):null;
    const tags = useDict(anot.tags, changes);

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
            var body = { meta: meta.dict, graphemes: graphemes.list,
                         edges: edges.list };
        } else {
            var body = { meta: meta.dict, tags: tags.dict };
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

    const runFunction = fun_name => {
        if (changes.dirty>0 && 
            !confirm(Text['warning_save'])) {
            return;
        }
        fetch(`api/run/${fun_name}/${id.full}`)
        .then(r => {
            if (r.ok) {
                return r.json();
            } else throw r;
        }).then(data => {
            meta.set(data.meta, 'UPD_META_ALL');
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
                tags.set(data.tags, 'UPD_TAGS_ALL');
            }
        }).catch(setError);
    };

    return html`
        <${Header} ...${{title, id, links, saveChanges,
            message, show_save: changes.dirty>0, runFunction,
            functions, changes }} />
        <${TagEditor} schema=${is_logo?l_tags:g_tags}
            ...${{meta_tags, flags, meta, tags }} />
        ${is_logo?
            html`<${LogogramEditor} ...${{id, graphemes, edges, g_tags,
                e_tags, color_list, changes}} />`
            :html`<${GraphemeEditor} ...${{id}} />`}
        <pre>${annotation_help}</pre>
    `;
}

function Header ({ title, id, links, saveChanges, message, show_save,
    functions, runFunction, changes }) {
    const [ selected, setSelected ] = useSavedState('last_function', '');
    return html`<header>
        <a href="">${title}</a> » 
        <a href="list/${id.dir}">${id.dir}</a> » ${id.num}
        <a href="edit/${id.dir}/${links.prev}">⬅️</a>
        <a href="edit/${id.dir}/${links.next}" tabIndex=3 >➡️</a>
        ${changes.some?html`<button onclick=${changes.undo}>↩️</button>`:null}
        ${show_save?html`<button tabIndex=2
            onclick=${saveChanges} >💾</button>`:null}
        <span class="message_text">${message}</span>
        ${functions.length>0?html`
            <select onchange=${e => setSelected(e.target.value)} value=${selected}>
                ${functions.map(e=>html`<option value=${e}>${e}</option>`)}
            </select>
            <button disabled=${selected==''} onclick=${() => runFunction(selected)}>⚙️</button>
        `:null}
    </header>`;
}

function TagEditor ({ meta_tags, meta, schema, tags, flags }) {
    const text_tags = meta_tags.filter(t => flags[t]==undefined);
    return html`<table class="TagEditor">
        ${text_tags.map((k, i) => html`<tr
            class=${i==text_tags.length-1?'last':''}>
            ${i>0?html`<th></th>`:html`<th>${Text['meta']}</th>`}
            <th>${k}:</th>
            <td><textarea rows="1" autocomplete="off"
                oninput=${e => meta.update(k, e.target.value, `UPD_META_${k}`)}
                value=${meta.dict[k] || ''} />
            </td>
        </tr>`)}
        ${schema.map((t, i) => html`<tr
            class=${`${i==0?'first':''} ${i==schema.length-1?'last':''}`}>
            ${i>0?html`<th></th>`:html`<th>${Text['tags']}</th>`}
            <th>${t}:</th>
            <td><input type=text value=${tags.dict[t] || ''}
                oninput=${e => tags.update(c, e.target.value, `TAG_${t}_UPD`)}
            /></td>
        </tr>`)}
        <tr class="first">
            <th colspan="2"></th><td>${Object.keys(flags).map(f => html`<span class="flag">
            <input type="checkbox"
                onchange=${() => meta.update(f, !meta.dict[f], `UPD_META_${f}`)}
                checked=${!!meta.dict[f]} /> ${flags[f]}
        </span>`)}</td></tr>
    </table>`;
}
