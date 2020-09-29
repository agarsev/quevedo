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
            setList(nl);
            cb();
        },
        update: (i, v) => {
            let nl = list.slice(); nl[i] = v;
            setList(nl);
            cb();
        },
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

function SymbolList ({ symbols }) {

    //let [ current_box, setCurrentBox ] = useState(null); // symbol being edited
    const colors = useList(symbols.list.map((_,i) =>
        color_list[i%color_list.length]))

    const removeSymbol = i => {
        symbols.remove(i);
        colors.remove(i);
    };

    const transcr = useRef(null);

    return html`
        <div id="boxes">
            <img ref=${transcr} id="transcr" src="${mount_path}img/${t_id}.png"/>
            ${symbols.list.map((s, i) => html`<${BBox}
                    x=${s.box[0]} y=${s.box[1]}
                    w=${s.box[2]} h=${s.box[3]}
                    color=${colors.list[i]} image_rect=${transcr}
            />`)}
        </div>
        <ul id="symbol_list">${symbols.list.map((s, i) => html`<li>
            <${SymbolEntry} name=${s.name || ''}
                changeName=${name => symbols.update(i, { ...s, name})}
                color=${colors.list[i]} changeColor=${c => colors.update(i, c)}
                remove=${() => removeSymbol(i)}
            /></li>`)}
        </ul>
    `;
}

function SymbolEntry ({ name, remove, changeName, color, changeColor }) {
    return html`
        <input type=color value=${color}
            oninput=${e => changeColor(e.target.value)} />
        <input type=text tabIndex=1 value=${name}
            oninput=${e => changeName(e.target.value)}/>
        <button>📐</button>
        <button onclick=${remove}>🗑️</button>
    `;
}

function BBox ({ x, y, w, h, color, image_rect }) {
    const rect = useRef(null);
    const [left, setLeft] = useState(-10);
    const [top, setTop] = useState(-10);
    const [width, setWidth] = useState(0);
    const [height, setHeight] = useState(0);

    if (x === undefined) return null;

    const reflow = () => {
        const { width, height } = image_rect.current.getBoundingClientRect();
        if (width > 10) {
            setLeft(Math.round((x-w/2.0)*width)+'px');
            setTop(Math.round((y-h/2.0)*height)+'px');
            setWidth(Math.round(w*1.0*width)+'px');
            setHeight(Math.round(h*1.0*height)+'px');
        } else { setTimeout(reflow, 50); }
    };
    useEffect(() => setTimeout(reflow, 100), []); // I don't know a better way to ensure image is rendered...

    return html`<span ref=${rect} class=anot
        style="left: ${left}; top: ${top}; width: ${width}; height: ${height}; border-color: ${color};"
    />`;
}

/*
window.onload = function () {

        // List of symbols
        
        const trans = document.getElementById("transcr");
        const boxes_layer = document.getElementById("boxes");

        const symbol_list = document.getElementById("symbol_list");
        function add_symbol (sym) {
            const li = document.createElement("li");
            if (sym !== undefined) {
                li.innerHTML = `<symbol-entry name="${sym.name}"
                    x="${sym.box[0]}" y="${sym.box[1]}"
                    w="${sym.box[2]}" h="${sym.box[3]}"/>`;
            } else {
                li.innerHTML = "<symbol-entry />";
            }
            symbol_list.appendChild(li);
            mark_dirty();
            return li.firstChild;
        }
        class SymbolEntry extends HTMLElement {
            constructor () {
                super();
				const rect = create(boxes_layer, 'span', { class: 'anot' });
                this.rect = rect;
                const x = this.getAttribute('x');
                if (x !== undefined) {
                    const y = this.getAttribute('y');
                    const w = this.getAttribute('w');
                    const h = this.getAttribute('h');
                }
				rect.dirty_box = false;
                current_box = rect;
                edit.onclick = () => {
                    rect.style.width = 0;
                    rect.style.height = 0;
                    current_box = rect;
                    mark_dirty();
                };
            }
        }

        // Bounding boxes of symbols

        let draw = null;
        trans.addEventListener('mousedown', e => {
            if (!current_box) add_symbol();
			current_box.dirty_box = true;
            const { left, top } = trans.getBoundingClientRect();
            const x = e.clientX - left;
            const y = e.clientY - top;
            draw = { x, y };
            current_box.style.left = x+'px';
            current_box.style.top = y+'px';
            current_box.style.width = 0;
            current_box.style.height = 0;
            e.preventDefault();
        });
        trans.addEventListener('mousemove', e => {
            if (draw !== null) {
                const { left, top } = trans.getBoundingClientRect();
                const x = e.clientX - left;
                const y = e.clientY - top;
                if (x >= draw.x) {
                    current_box.style.left = draw.x+'px';
                    current_box.style.width = x-draw.x+'px';
                } else {
                    current_box.style.left = x+'px';
                    current_box.style.width = draw.x-x+'px';
                }
                if (y >= draw.y) {
                    current_box.style.top = draw.y+'px';
                    current_box.style.height = y-draw.y+'px';
                } else {
                    current_box.style.top = y+'px';
                    current_box.style.height = draw.y-y+'px';
                }
            }
        });
        document.addEventListener('mouseup', () => {
            current_box = null;
            draw = null;
        });

		current_box = null;

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
