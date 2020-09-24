import { html, render } from 'https://unpkg.com/htm/preact/index.mjs?module'

let mount_path = '';

function App ({ title, path, description, trans_list }) {
    return html`
        <${Header} />
        <${MeaningList} />
        <h2>Symbols (drag to draw)</h2>
        <div id="symbols">
            <${BoxesArea} />
            <${SymbolList} />
        </div>
        <pre>${info.annotation_help}</pre>
    `;
}

function Header ({ id, prev_link, next_link }) {
    return html`<h1>
        <a href=${prev_link}>⬅️</a>
        <a href=${mount_path}>⬆️</a>
        ${id}
        <a href=${next_link} tabIndex=3 >➡️</a>
        <button id=save tabIndex=2 >💾</button>
        <span id=message_text ></span>
        <button id=auto >⚙️</button>
    </h1>`;
}

function MeaningList ({ meanings }) {
    return html`<div id="meanings">
        <h2>Meanings <button id="add_meaning">➕</button></h2>
        <ul id="meaning_list">
            ${meanings.map(m => html`<li>
                <${MeaningEntry} value="${m}" />
            </li>`)}
        </ul>
    </div>`;
}

function BoxesArea ({ id }) {
    return html`<div>
        <div id="boxes">
            <img id="transcr" src="${mount_path}img/${id}.png"/>
        </div>
    </div>`;
}

function SymbolList ({ symbols }) {
    return html`<ul id="symbol_list">
        ${symbols.map(s => html`<li>
            <${SymbolEntry} name="${s.name}" x="${s.box[0]}" y="${s.box[1]}"
                     w="${s.box[2]}" h="${s.box[3]}" />
        </li>`)}
    </ul>`;
}

// TODO: get transcription number from url

fetch('/api/transcription/${id}').then(r => r.json()).then(data => {
    document.title = `${document.title}: ${data.title} (${id})`;
    mount_path = data.mount_path;
    render(html`<${App} ...${data} />`, document.body);
});

window.onload = function () {
        let dirty = false;
        const save_button = document.getElementById("save");
        save_button.style.visibility = 'hidden';
        function mark_dirty () {
            save_button.style.visibility = '';
            dirty = true;
        }
        function mark_clean () { dirty = false; }
        window.addEventListener('beforeunload', e => {
            if (dirty) {
                e.preventDefault();
                e.returnValue = "Warning: unsaved changes will be lost";
            }
        });

        /* Helper for creating DOM elements */
        function create (parent, tag, attrs, inner) {
            const el = document.createElement(tag);
            for (key in attrs) {
                el.setAttribute(key, attrs[key]);
            }
            if (inner) el.innerHTML = inner;
            parent.appendChild(el);
            return el;
        }

        /* List of meanings for the transcribed sign */

        const meaning_list = document.getElementById("meaning_list");
        const meaning_list_button = document.getElementById("add_meaning");
        meaning_list_button.addEventListener("click", function () {
            const li = document.createElement("li");
            li.innerHTML = "<meaning-entry />";
            meaning_list.appendChild(li);
            mark_dirty();
        });
        class MeaningEntry extends HTMLElement {
            constructor () {
                super();
                this.text = create(this, 'input', { type: 'text',
                    value: this.getAttribute('value') || '' });
                this.text.oninput = mark_dirty;
                const del = create(this, 'button', {}, '🗑️');
                del.onclick = () => {
                    mark_dirty();
                    meaning_list.removeChild(this.parentElement);
                };
            }
        }
        customElements.define('meaning-entry', MeaningEntry);

        /* List of symbols */
        
        const trans = document.getElementById("transcr");
        const boxes_layer = document.getElementById("boxes");
        let current_box = null; // symbol being edited

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
        const color_list = [ '#FF0000', '#00FF00', '#0000FF', '#FF00FF',
            '#00FFFF', '#880000', '#008800', '#000088', '#888800', '#008888' ];
        let i = 0;
        class SymbolEntry extends HTMLElement {
            constructor () {
                super();
                const color_val = color_list[(i++)%color_list.length];
                const col = create(this, 'input', { type: 'color', value: color_val });
                const text = create(this, 'input', { type: 'text', tabIndex: 1,
					value: this.getAttribute('name') || '' });
                this.text = text;
                const edit = create(this, 'button', {}, '📐');
                const del = create(this, 'button', {}, '🗑️');
				const rect = create(boxes_layer, 'span', { class: 'anot' });
                this.rect = rect;
                const x = this.getAttribute('x');
                if (x !== undefined) {
                    const y = this.getAttribute('y');
                    const w = this.getAttribute('w');
                    const h = this.getAttribute('h');
                    const { width, height } = trans.getBoundingClientRect();
                    rect.style.left = Math.round((x-w/2.0)*width)+'px';
                    rect.style.top = Math.round((y-h/2.0)*height)+'px';
                    rect.style.width = Math.round(w*1.0*width)+'px';
                    rect.style.height = Math.round(h*1.0*height)+'px';
                }
				rect.style.borderColor = color_val;
				rect.dirty_box = false;
                boxes_layer.appendChild(rect);
                text.oninput = mark_dirty;
                col.oninput = () => rect.style.borderColor = col.value;
                current_box = rect;
                edit.onclick = () => {
                    rect.style.width = 0;
                    rect.style.height = 0;
                    current_box = rect;
                    mark_dirty();
                };
                del.onclick = () => this.removeSelf();
            }
            removeSelf () {
                symbol_list.removeChild(this.parentElement);
                boxes_layer.removeChild(this.rect);
                mark_dirty();
            }
        }
        customElements.define('symbol-entry', SymbolEntry);

        /* Bounding boxes of symbols */

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

        /* saving */

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
        /* loading of automatic annotations */
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
