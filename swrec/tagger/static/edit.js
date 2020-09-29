const html = htm.bind(preact.h);
const { useState, useEffect, useRef } = preactHooks;


let mount_path = '';
let t_id  = (new URL(document.location)).hash.substring(1);
window.onhashchange = () => window.location.reload();


function useList (initial_value, cb = () => null) {
    const [ list, setList ] = useState(initial_value);
    return { list,
        add: v => {
            setList(list.concat([v]));
            cb();
        },
        remove: i => {
            let nl = list.slice(); nl.splice(i, 1);
            setList(nl); cb();
        },
        update: (i, v) => {
            let nl = list.slice(); nl[i] = v;
            setList(nl); cb();
        },
        update_fn: (i, fn) => {
            let nl = list.slice(); nl[i] = fn(list[i]);
            setList(nl); cb();
        }
    };
}

fetch(`/api/transcriptions/${t_id}`).then(r => r.json()).then(data => {
    document.title = `${document.title}: ${data.title} (${t_id})`;
    mount_path = data.mount_path;
    preact.render(html`<${App} ...${data} />`, document.body);
});

function App ({ annotation_help, mount_path, links, anot }) {

    /* Prevent loss of changes by unintentional page unloading */
    const [ dirty, setDirty ] = useState(false);
    const markDirty = () => setDirty(true);
    useEffect(() => {
        window.addEventListener('beforeunload', e => {
            if (dirty) {
                e.preventDefault();
                e.returnValue = "Warning: unsaved changes will be lost";
            }
        });
    });

    const meanings = useList(anot.meanings, markDirty)
    const symbols = useList(anot.symbols, markDirty)

    return html`
        <${Header} ...${{mount_path, links, dirty}} />
        <${MeaningList} ...${{meanings}} />
        <h2>Symbols (drag to draw)</h2>
        <div id="symbols">
            <${SymbolList} ...${{symbols}} />
        </div>
        <pre>${annotation_help}</pre>
    `;
}

function Header ({ mount_path, links, dirty }) {
    return html`<h1>
        <a href="edit.html#${links.prev}">⬅️</a>
        <a href=${mount_path}>⬆️</a>
        ${t_id}
        <a href="edit.html#${links.next}" tabIndex=3 >➡️</a>
        ${dirty?html`<button id=save tabIndex=2 >💾</button>`:null}
        <span id=message_text ></span>
        <button id=auto >⚙️</button>
    </h1>`;
}

function MeaningList ({ meanings }) {
    return html`<div id="meanings">
        <h2>Meanings
            <button id="add_meaning" onclick=${() => meanings.add()}>➕</button>
        </h2>
        <ul id="meaning_list">
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

function SymbolList ({ symbols }) {

    const colors = useList(() => symbols.list.map(getNextColor));

    const removeSymbol = i => {
        symbols.remove(i);
        colors.remove(i);
    };

    // Symbol being currently edited (object with idx (array index), start_x and
    // start_y of rectangle being drawn
    const [ editing_symbol, setEditing ] = useState(null);

    return html`
        <${Annotation} ...${{symbols, colors, editing_symbol, setEditing}} />
        <ul id="symbol_list">${symbols.list.map((s, i) => html`
            <li class=${editing_symbol !== null &&
                    editing_symbol.idx === i?'editing':''}>
                <${SymbolEntry} name=${s.name || ''}
                    changeName=${name => symbols.update(i, { ...s, name})}
                    color=${colors.list[i]} changeColor=${c => colors.update(i, c)}
                    remove=${() => removeSymbol(i)}
                    editBox=${() => setEditing({ idx: i })}
                />
            </li>`)}
        </ul>
    `;
}

function SymbolEntry ({ name, remove, changeName, color, changeColor, editBox }) {
    return html`
        <input type=color value=${color}
            oninput=${e => changeColor(e.target.value)} />
        <input type=text tabIndex=1 value=${name}
            oninput=${e => changeName(e.target.value)}/>
        <button onclick=${editBox}>📐</button>
        <button onclick=${remove}>🗑️</button>
    `;
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
            symbols.add({ box: [0,0,0,0] });
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
    useEffect(() => {
        document.addEventListener('mouseup', () => setEditing(null))
    }, []);

    return html`<div id="boxes">
        <img src="${mount_path}img/${t_id}.png"
            ref=${image_rect} id="transcr" 
            onmousedown=${mouse_down}
            onmousemove=${mouse_move}
        />
        ${symbols.list.map((s, i) => html`<${BBox}
                x=${s.box[0]} y=${s.box[1]}
                w=${s.box[2]} h=${s.box[3]}
                color=${colors.list[i]}
                image_width=${image_width}
                image_height=${image_height}
        />`)}
    </div>`;
}

function BBox ({ x, y, w, h, color, image_width, image_height }) {

    if (x === undefined) return null;
    const left = Math.round((x-w/2.0)*image_width)+'px';
    const top = Math.round((y-h/2.0)*image_height)+'px';
    const width = Math.round(w*1.0*image_width)+'px';
    const height = Math.round(h*1.0*image_height)+'px';

    return html`<span class=anot style=${`
        left: ${left}; top: ${top};
        width: ${width}; height: ${height};
        border-color: ${color};`} />`;
}

/*
window.onload = function () {

        // saving

        const msg = document.getElementById("message_text");
        save_button.onclick = function () {
            msg.innerHTML = "Saving...";
            const data = {
                meanings: [],
                symbols: []
            };
            meaning_list.querySelectorAll("meaning-entry").forEach(m => {
                data.meanings.push(m.text.value);
            });
			const { left: off_x, top: off_y } = trans.getBoundingClientRect();
			const { clientWidth: off_w, clientHeight: off_h } = trans;
            symbol_list.querySelectorAll("symbol-entry").forEach(s => {
				let box;
				if (s.rect.dirty_box) {
                	const r = s.rect.getBoundingClientRect();
					const { clientWidth: w, clientHeight: h } = s.rect;
                    box = [ (r.left+w/2.0-off_x)/off_w,
                        (r.top+h/2.0-off_y)/off_h,
                        w*1.0/off_w, h*1.0/off_h ];
				} else {
					box = [ s.getAttribute('x'), s.getAttribute('y'),
							s.getAttribute('w'), s.getAttribute('h') ];
				}
                data.symbols.push({ name: s.text.value, box });
            });
            fetch(window.location, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            })
            .then(r => {
                if (r.ok) {
                    msg.innerHTML = "Saved";
                    mark_clean();
                } else throw r.statusText;
            })
            .catch(e => msg.innerHTML = `Error: ${e}`);
        }

        const auto_url = (window.location+'').replace(/edit/, 'auto');
        // loading of automatic annotations
        document.getElementById('auto').onclick = function () {
            let sl = symbol_list.querySelectorAll('symbol-entry');
            if (sl.length>0 && !confirm("WARNING: Existing annotations will be removed"))
                return;
            sl.forEach(el => el.removeSelf());
            fetch(auto_url).then(r => {
                if (r.ok) {
                    return r.json();
                } else throw r.statusText;
            }).then(({ symbols }) => {
                console.log(symbols);
                symbols.forEach(s => add_symbol(s));
            })
            .catch(e => msg.innerHTML = `Error: ${e}`);
        }
    }
*/
