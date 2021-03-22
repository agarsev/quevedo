// 2021-03-22 Antonio F. G. Sevilla <afgs@ucm.es>

const html = htm.bind(preact.h);
const { useState, useEffect, useRef } = preactHooks;

import Text from './i18n.js';
import { useList } from './common_state.js';

const color_list = [ '#FF0000', '#00FF00', '#0000FF', '#FF00FF',
    '#00FFFF', '#880000', '#008800', '#000088', '#888800', '#008888' ];
let next_color = 0;
function getNextColor () {
    const r = color_list[next_color];
    next_color = (next_color + 1) % color_list.length;
    return r;
}

export function TranscriptionEditor (props) {
    return html`
        <h2>${Text['symbols']}</h2>
        <${SymbolList} ...${props} />
    `;
}

function SymbolList ({ id, symbols, columns }) {

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
        <${Annotation} ...${{id, symbols, colors, editing_symbol, setEditing}} />
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
                        symbols.update_fn(i, s => ({ ...s, tags: ntags }),
                            `SYMB_${i}_UPD_TAG_${t_id}`);
                    }}
                    columns=${columns}
                    color=${colors.list[i]} changeColor=${c => colors.update(i, c)}
                    remove=${() => removeSymbol(i)}
                    markEditing=${e => {
                        setEditing({ idx: i });
                        e.stopPropagation();
                    }}
                    editing=${current}
                    navigate=${e => { switch(e.key) {
                        case "Enter": setEditing(null); break;
                        case "ArrowDown": {
                            let ts = Array.from(document.querySelectorAll(".SymbolEntry input[type=text]"));
                            let act = ts.findIndex(el => el==document.activeElement);
                            let nx = act+columns.length;
                            if (nx < ts.length) ts[nx].focus();
                            break; }
                        case "ArrowUp": {
                            let ts = Array.from(document.querySelectorAll(".SymbolEntry input[type=text]"));
                            let act = ts.findIndex(el => el==document.activeElement);
                            let nx = act-columns.length;
                            if (nx >= 0) ts[nx].focus();
                            break; }
                        default: return;
                        }
                        e.stopPropagation();
                        e.preventDefault();
                    }}
                />`;
            })}</tbody>
        </table></div>
    </div>`;
}

function SymbolEntry ({ tags, changeTag, columns, remove,
        color, changeColor, markEditing, editing, navigate }) {
    return html`<tr class=${`SymbolEntry ${editing?'editing':''}`}
        onmousedown=${markEditing}>
        <td><input type=color value=${color}
            oninput=${e => changeColor(e.target.value)} /></td>
        ${columns.map((c, i) => html`<td><input type=text
            placeholder=${c} tabIndex=1 value=${tags[i]}
            oninput=${e => changeTag(i, e.target.value)}
            onkeydown=${navigate}
            onfocus=${markEditing} /></td>`)}
        <td><button onclick=${remove}>🗑️</button></td>
    </tr>`;
}

function Annotation ({ id, symbols, colors, editing_symbol, setEditing }) {

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
            editing_symbol = { idx: symbols.list.length };
            symbols.add({ box: [0,0,0,0], tags: [] },
                `SYMB_${editing_symbol.idx}_UPD_BOX`);
            colors.add(getNextColor());
        } else {
            editing_symbol = { ...editing_symbol }; // should be cloned
        }
        const { left, top } = image_rect.current.getBoundingClientRect();
        editing_symbol.start_x = e.clientX - left;
        editing_symbol.start_y = e.clientY - top;
        symbols.update_fn(editing_symbol.idx, s => ({ ...s, box: [
            editing_symbol.start_x/image_width, editing_symbol.start_y/image_height,
            0,0] }), `SYMB_${editing_symbol.idx}_UPD_BOX`);
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
        ] }), `SYMB_${editing_symbol.idx}_UPD_BOX`);
        e.preventDefault();
    }

    return html`<div class="Annotation">
        <img src="img/${id.full}.png"
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
