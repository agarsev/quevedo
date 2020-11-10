import Text from './i18n.js';

const html = htm.bind(preact.h);
const { useState, useEffect, useRef } = preactHooks;


let mount_path = '';
let t_id  = (new URL(document.location)).hash.substring(1);
window.onhashchange = () => window.location.reload();


function useList (initial_value, cb = () => null) {
    const [ list, setList ] = useState(initial_value);
    const set = l => { setList(l); cb(); }
    return { list, set,
        add: v => set(list.concat([v])),
        remove: i => {
            let nl = list.slice(); nl.splice(i, 1);
            set(nl);
        },
        update: (i, v) => {
            let nl = list.slice(); nl[i] = v;
            set(nl);
        },
        update_fn: (i, fn) => {
            let nl = list.slice(); nl[i] = fn(list[i]);
            set(nl);
        }
    };
}

fetch(`api/transcriptions/${t_id}`).then(r => r.json()).then(data => {
    document.title = `${document.title}: ${data.title} (${t_id})`;
    mount_path = data.mount_path;
    preact.render(html`<${App} ...${data} />`, document.body);
});

function preventLostChanges (e) {
    e.preventDefault();
    e.returnValue = Text['warning_save'];
}

function App ({ annotation_help, mount_path, links, anot, columns, exp_list }) {

    /* Prevent loss of changes by unintentional page unloading:
     * 0: no changes/all changes saved
     * 1: changes done
     * 2: changes submitted to server
     */
    const [ dirty, setDirty ] = useState(0);
    const markDirty = () => setDirty(1);
    useEffect(() => {
        if (dirty>0) {
            window.addEventListener('beforeunload', preventLostChanges);
            return () => window.removeEventListener('beforeunload', preventLostChanges);
        }
    }, [dirty]);

    const meanings = useList(anot.meanings, markDirty)
    const symbols = useList(anot.symbols, markDirty)

    const [ message, setMessage ] = useState('');
    const setError = resp => {
        if (resp.status < 500) {
            resp.text().then(e => setMessage(`${Text['error']}: ${e}`));
        } else {
            setMessage(`${Text['error']}: ${resp.statusText}`);
        }
    }

    const saveChanges = () => {
        setDirty(2);
        setMessage(Text['saving']);
        fetch(`api/transcriptions/${t_id}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                meanings: meanings.list,
                symbols: symbols.list
            })
        }).then(r => {
            if (r.ok) {
                setDirty(0);
                setMessage(Text['saved']);
            } else throw r;
        }).catch(setError);
    };

    const autoAnnotate = experiment => {
        if (symbols.list.length > 0 && 
            !confirm(Text['confirm_generate'])) {
            return;
        }
        fetch(`api/auto_annotate/${t_id}${experiment?`?exp=${experiment}`:''}`)
        .then(r => {
            if (r.ok) {
                return r.json();
            } else throw r;
        }).then(data => {
            console.log(data);
            let new_symbols = data.symbols.map(({ box, name }) => {
                let tags = [];
                tags[data.tag_index] = name;
                return { box, tags };
            });
            // sort left-to-right (roughly) and top-to-bottom (strict)
            new_symbols.sort((a, b) => {
                let left_a = a.box[0]-a.box[2]/2;
                let left_b = b.box[0]-b.box[2]/2;
                if (Math.abs(left_b-left_a)<0.09) {
                    let top_a = a.box[1]-a.box[3]/2;
                    let top_b = b.box[1]-b.box[3]/2;
                    return top_a - top_b;
                } else return left_a - left_b;
            });
            symbols.set(new_symbols);
        }).catch(setError);
    };

    return html`
        <${Header} ...${{mount_path, links, saveChanges,
            message, show_save: dirty>0, autoAnnotate,
            exp_list }} />
        <${MeaningList} ...${{meanings}} />
        <h2>${Text['symbols']}</h2>
        <${SymbolList} ...${{symbols, columns}} />
        <pre>${annotation_help}</pre>
    `;
}

function Header ({ mount_path, links, saveChanges, message, show_save,
    exp_list, autoAnnotate }) {

    const exp_select = useRef({ value: null });

    return html`<header>
        <a href="edit.html#${links.prev}">⬅️</a>
        <a href=${mount_path}>⬆️</a>
        ${t_id}
        <a href="edit.html#${links.next}" tabIndex=3 >➡️</a>
        ${show_save?html`<button tabIndex=2
            onclick=${saveChanges} >💾</button>`:null}
        <span class="message_text">${message}</span>
        ${exp_list.length<2?null:html`<select ref=${exp_select}>
            ${exp_list.map(e=>html`<option value=${e}>${e}</option>`)}
        </select>`}
        <button onclick=${() => autoAnnotate(exp_select.current.value)}>⚙️</button>
    </header>`;
}

function MeaningList ({ meanings }) {
    return html`<div class="MeaningList">
        <h2>${Text['meanings']}
            <button onclick=${() => meanings.add()}>➕</button>
        </h2>
        <ul>
            ${meanings.list.map((m, i) => html`<li>
                <${MeaningEntry} value=${m}
                    change=${val => meanings.update(i, val)}
                    remove=${() => meanings.remove(i)} />
            </li>`)}
        </ul>
    </div>`;
}

function MeaningEntry ({ value, remove, change }) {
    return html`
        <input type="text" value=${value}
            oninput=${e => change(e.target.value)} />
        <button onclick=${remove}>🗑️</button>
    `;
}

const color_list = [ '#FF0000', '#00FF00', '#0000FF', '#FF00FF',
    '#00FFFF', '#880000', '#008800', '#000088', '#888800', '#008888' ];
let next_color = 0;
function getNextColor () {
    const r = color_list[next_color];
    next_color = (next_color + 1) % color_list.length;
    return r;
}

function SymbolList ({ symbols, columns }) {

    const colors = useList([]);
    if (colors.list.length < symbols.list.length) {
        next_color = 0;
        colors.set(symbols.list.map(getNextColor));
    }

    // Symbol being currently edited (object with idx (array index), start_x and
    // start_y of rectangle being drawn
    const [ editing_symbol, setEditing ] = useState(null);
    useEffect(() => {
        // on mouse up, we stop drawing but keep selected box
        document.addEventListener('mouseup', () =>
            setEditing(es => es!=null?({ idx: es.idx }):null))
        // on mouse down outside the annotation, we stop drawing
        document.addEventListener('mousedown', () => setEditing(null));
    }, []);

    const removeSymbol = i => {
        setEditing(null);
        symbols.remove(i);
        colors.remove(i);
    };

    return html`<div class="SymbolList">
        <${Annotation} ...${{symbols, colors, editing_symbol, setEditing}} />
        <div><table>
            <thead><tr><th />
                ${columns.map(c => html`<th>${c}</th>`)}
                <th />
            </tr></thead>
            <tbody>${symbols.list.map((s, i) => {
                const current = editing_symbol !== null && editing_symbol.idx === i;
                return html`<${SymbolEntry} tags=${s.tags || []}
                    changeTag=${(t_id, t_val) => {
                        let ntags = s.tags?s.tags.slice():[];
                        ntags[t_id] = t_val;
                        symbols.update_fn(i, s => ({ ...s, tags: ntags }));
                    }}
                    columns=${columns}
                    color=${colors.list[i]} changeColor=${c => colors.update(i, c)}
                    remove=${() => removeSymbol(i)}
                    markEditing=${e => {
                        setEditing({ idx: i });
                        e.stopPropagation();
                    }}
                    editing=${current}
                />`;
            })}</tbody>
        </table></div>
    </div>`;
}

function SymbolEntry ({ tags, changeTag, columns, remove,
        color, changeColor, markEditing, editing }) {
    return html`<tr class=${`SymbolEntry ${editing?'editing':''}`}
        onmousedown=${markEditing}>
        <td><input type=color value=${color}
            oninput=${e => changeColor(e.target.value)} /></td>
        ${columns.map((c, i) => html`<td><input type=text
            placeholder=${c} tabIndex=1 value=${tags[i]}
            oninput=${e => changeTag(i, e.target.value)}
            onfocus=${markEditing} /></td>`)}
        <td><button onclick=${remove}>🗑️</button></td>
    </tr>`;
}

function Annotation ({ symbols, colors, editing_symbol, setEditing }) {

    // Image bounding rectangle 
    const image_rect = useRef(null);
    const [ image_width, setImageW ] = useState(0);
    const [ image_height, setImageH ] = useState(0);
    const reflow = () => {
        const { width, height } = image_rect.current.getBoundingClientRect();
        if (width > 10) {
            setImageW(width);
            setImageH(height);
        } else { setTimeout(reflow, 50); }
    };
    // I don't know a better way to wait for the image to be rendered
    useEffect(() => setTimeout(reflow, 100), []);

    const mouse_down = e => {
        if (editing_symbol === null) {
            symbols.add({ box: [0,0,0,0], tags: [] });
            colors.add(getNextColor());
            editing_symbol = { idx: symbols.list.length };
        } else {
            editing_symbol = { ...editing_symbol }; // should be cloned
        }
        const { left, top } = image_rect.current.getBoundingClientRect();
        editing_symbol.start_x = e.clientX - left;
        editing_symbol.start_y = e.clientY - top;
        symbols.update_fn(editing_symbol.idx, s => ({ ...s, box: [
            editing_symbol.start_x/image_width, editing_symbol.start_y/image_height,
            0,0] }));
        setEditing(editing_symbol);
        e.preventDefault();
        e.stopPropagation();
    };
    const mouse_move = e => {
        if (editing_symbol === null) return;
        if (editing_symbol.start_x === undefined) return;
        const { left, top } = image_rect.current.getBoundingClientRect();
        const mx = e.clientX - left;
        const my = e.clientY - top;
        const bw = mx - editing_symbol.start_x;
        const bh = my - editing_symbol.start_y;
        symbols.update_fn(editing_symbol.idx, s => ({ ...s, box: [
            (editing_symbol.start_x + bw/2)/image_width, // x
            (editing_symbol.start_y + bh/2)/image_height, // y
            (bw>=0?bw:-bw)/image_width, // w
            (bh>=0?bh:-bh)/image_height, // h
        ] }));
        e.preventDefault();
    }

    return html`<div class="Annotation">
        <img src="${mount_path}img/${t_id}.png"
            ref=${image_rect}
            onmousedown=${mouse_down}
            onmousemove=${mouse_move}
        />
        ${symbols.list.map((s, i) => html`<${BBox}
                x=${s.box[0]} y=${s.box[1]}
                w=${s.box[2]} h=${s.box[3]}
                color=${colors.list[i]}
                image_width=${image_width}
                image_height=${image_height}
                current=${editing_symbol && editing_symbol.idx==i}
        />`)}
    </div>`;
}

function BBox ({ x, y, w, h, color, image_width, image_height, current }) {

    if (x === undefined) return null;
    const left = Math.round((x-w/2.0)*image_width)+'px';
    const top = Math.round((y-h/2.0)*image_height)+'px';
    const width = Math.round(w*1.0*image_width)+'px';
    const height = Math.round(h*1.0*image_height)+'px';

    return html`<span class=${`BBox ${current?'editing':''}`} style=${`
        left: ${left}; top: ${top};
        width: ${width}; height: ${height};
        border-color: ${color};`} />`;
}
