// 2021-03-22 Antonio F. G. Sevilla <afgs@ucm.es>
// Licensed under the Open Software License version 3.0

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

export function LogogramEditor (props) {
    return html`
        <h2>${Text['logogram_annotation']}</h2>
        <${GraphemeList} ...${props} />
    `;
}

function GraphemeList ({ id, graphemes, columns }) {

    const colors = useList([]);
    if (colors.list.length < graphemes.list.length) {
        next_color = 0;
        colors.set(graphemes.list.map(getNextColor));
    }

    // Grapheme being currently edited (object with idx (array index), start_x and
    // start_y of rectangle being drawn
    const [ editing_grapheme, setEditing ] = useState(null);
    useEffect(() => {
        // on mouse up, we stop drawing but keep selected box
        document.addEventListener('mouseup', () =>
            setEditing(es => es!=null?({ idx: es.idx }):null))
        document.addEventListener('touchend', () =>
            setEditing(es => es!=null?({ idx: es.idx }):null))
        // on mouse down outside the annotation, we stop drawing
        document.addEventListener('mousedown', () => setEditing(null));
        document.addEventListener('touchstart', () => setEditing(null));
    }, []);

    const removeGrapheme = i => {
        setEditing(null);
        graphemes.remove(i);
        colors.remove(i);
    };

    return html`<div class="GraphemeList">
        <${Annotation} ...${{id, graphemes, colors, editing_grapheme, setEditing}} />
        <div><table>
            <thead><tr><th />
                ${columns.map(c => html`<th>${c}</th>`)}
                <th />
            </tr></thead>
            <tbody>${graphemes.list.map((s, i) => {
                const current = editing_grapheme !== null && editing_grapheme.idx === i;
                return html`<${GraphemeEntry} tags=${s.tags || {}}
                    changeTag=${(k, v) => graphemes.update_fn(i,
                            s => ({ ...s, tags: {...s.tags, [k]: v}}),
                            `GRAPH_${i}_UPD_TAG_${k}`)}
                    columns=${columns}
                    color=${colors.list[i]} changeColor=${c => colors.update(i, c)}
                    remove=${() => removeGrapheme(i)}
                    markEditing=${e => {
                        setEditing({ idx: i });
                        e.stopPropagation();
                    }}
                    editing=${current}
                    navigate=${e => { switch(e.key) {
                        case "Enter": setEditing(null); break;
                        case "ArrowDown": {
                            let ts = Array.from(document.querySelectorAll(".GraphemeEntry input[type=text]"));
                            let act = ts.findIndex(el => el==document.activeElement);
                            let nx = act+columns.length;
                            if (nx < ts.length) ts[nx].focus();
                            break; }
                        case "ArrowUp": {
                            let ts = Array.from(document.querySelectorAll(".GraphemeEntry input[type=text]"));
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

function GraphemeEntry ({ tags, changeTag, columns, remove,
        color, changeColor, markEditing, editing, navigate }) {
    return html`<tr class=${`GraphemeEntry ${editing?'editing':''}`}
        onmousedown=${markEditing}>
        <td><input type=color value=${color}
            oninput=${e => changeColor(e.target.value)} /></td>
        ${columns.map(c => html`<td><input type=text
            placeholder=${c} tabIndex=1 value=${tags[c]}
            oninput=${e => changeTag(c, e.target.value)}
            onkeydown=${navigate}
            onfocus=${markEditing} /></td>`)}
        <td><button onclick=${remove}>🗑️</button></td>
    </tr>`;
}

function Annotation ({ id, graphemes, colors, editing_grapheme, setEditing }) {

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
        if (editing_grapheme === null) {
            editing_grapheme = { idx: graphemes.list.length };
            graphemes.add({ box: [0,0,0,0], tags: {} },
                `GRAPH_${editing_grapheme.idx}_UPD_BOX`);
            colors.add(getNextColor());
        } else {
            editing_grapheme = { ...editing_grapheme }; // should be cloned
        }
        const { left, top } = image_rect.current.getBoundingClientRect();
        const pos = e.type == 'touchstart' ? e.touches[0] : e;
        editing_grapheme.start_x = pos.clientX - left;
        editing_grapheme.start_y = pos.clientY - top;
        graphemes.update_fn(editing_grapheme.idx, s => ({ ...s, box: [
            editing_grapheme.start_x/image_width, editing_grapheme.start_y/image_height,
            0,0] }), `GRAPH_${editing_grapheme.idx}_UPD_BOX`);
        setEditing(editing_grapheme);
        e.preventDefault();
        e.stopPropagation();
    };
    const mouse_move = e => {
        if (editing_grapheme === null) return;
        if (editing_grapheme.start_x === undefined) return;
        const { left, top } = image_rect.current.getBoundingClientRect();
        const pos = e.type == 'touchmove' ? e.touches[0] : e;
        const mx = pos.clientX - left;
        const my = pos.clientY - top;
        const bw = mx - editing_grapheme.start_x;
        const bh = my - editing_grapheme.start_y;
        graphemes.update_fn(editing_grapheme.idx, s => ({ ...s, box: [
            (editing_grapheme.start_x + bw/2)/image_width, // x
            (editing_grapheme.start_y + bh/2)/image_height, // y
            (bw>=0?bw:-bw)/image_width, // w
            (bh>=0?bh:-bh)/image_height, // h
        ] }), `GRAPH_${editing_grapheme.idx}_UPD_BOX`);
        e.preventDefault();
    }

    return html`<div class="Annotation">
        <img src="img/${id.full}.png"
            ref=${image_rect}
            onmousedown=${mouse_down}
            onmousemove=${mouse_move}
            ontouchstart=${mouse_down}
            ontouchmove=${mouse_move}
        />
        ${graphemes.list.map((s, i) => html`<${BBox}
                x=${s.box[0]} y=${s.box[1]}
                w=${s.box[2]} h=${s.box[3]}
                color=${colors.list[i]}
                image_width=${image_width}
                image_height=${image_height}
                current=${editing_grapheme && editing_grapheme.idx==i}
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
