// 2021-03-22 Antonio F. G. Sevilla <afgs@ucm.es>
// Licensed under the Open Software License version 3.0

const html = htm.bind(preact.h);
const { useState, useEffect, useRef } = preactHooks;

import Text from './i18n.js';
import { useList, useSavedState } from './common_state.js';

let next_color = 0;
function getNextColor (color_list) {
    const r = color_list[next_color];
    next_color = (next_color + 1) % color_list.length;
    return r;
}

export function LogogramEditor ({ id, graphemes, edges, g_tags, color_list }) {

    // modes: select, draw, edges
    const [ mode, setMode ] = useSavedState('select');

    const colors = useList([]);
    colors.next = () => getNextColor(color_list);
    if (colors.list.length < graphemes.list.length) {
        next_color = 0;
        colors.set(graphemes.list.map(colors.next));
    }

    // Object being currently edited:
    // - if a grapheme: idx (array index), start_x and start_y if drawing box
    // - if an edge: start (array index), end_x and end_y if drawing line
    const [ being_edited, setEditing ] = useState(null);
    const stop_editing = () => setEditing(null);
    useEffect(() => {
        if (mode == 'draw') {
            // if drawing, on mouse up inside, we stop drawing but keep selected box. On mouse down out, stop
            const stop_but_keep = () => setEditing(es => es!=null?({ idx: es.idx }):null);
            document.addEventListener('mouseup', stop_but_keep);
            document.addEventListener('touchend', stop_but_keep);
            document.addEventListener('mousedown', stop_editing);
            document.addEventListener('touchstart', stop_editing);
            return () => {
                document.removeEventListener('mouseup', stop_but_keep);
                document.removeEventListener('touchend', stop_but_keep);
                document.removeEventListener('mousedown', stop_editing);
                document.removeEventListener('touchstart', stop_editing);
            };
        } else {
            // if not drawing, on mouse up, we stop editing
            document.addEventListener('mouseup', stop_editing);
            document.addEventListener('touchend', stop_editing);
            return () => {
                document.removeEventListener('mouseup', stop_editing);
                document.removeEventListener('touchend', stop_editing);
            };
        }
    }, [mode]);

    const removeGrapheme = i => {
        // TODO FIX EDGES
        setEditing(null);
        graphemes.remove(i);
        colors.remove(i);
    };

    const addEdge = (i, j) => {
        setEditing(null);
        if (i == j) return;
        if (edges.list.some(({ start, end }) => start == i && end == j)) return;
        edges.add({
            start: i,
            end: j,
            tags: {},
        });
    };

    function ModeRadio ({ value, label }) {
        return html`<label class="ModeRadio">
            <input type=radio name=mode 
            checked=${mode==value} onchange=${e => {
                setMode(value);
                e.stopPropagation();
            }} />
            ${label}
        </label>`;
    }

    return html`
        <h2 class="AnnotationHeader">${Text['annotation']}
            <${ModeRadio} value="select" label=${Text['select'] || 'select'} />
            <${ModeRadio} value="draw" label=${Text['draw'] || 'draw'} />
            <${ModeRadio} value="edges" label=${Text['edges'] || 'edges'} />
        </h2>
        <div class="GraphemeList">
        <${Annotation} ...${{id, graphemes, edges, colors, being_edited,
            setEditing, addEdge, mode}} />
        <${TagTable} editing_grapheme=${being_edited}
            ...${{g_tags, graphemes, colors, setEditing, removeGrapheme}} />
        </div>
    `;
}

function Annotation ({ id, graphemes, edges, colors, being_edited, setEditing, addEdge,
    mode }) {

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

    const start_rect_draw = e => {
        if (being_edited === null) {
            being_edited = { idx: graphemes.list.length };
            graphemes.add({ box: [0,0,0,0], tags: {} },
                `GRAPH_${being_edited.idx}_UPD_BOX`);
            colors.add(colors.next());
        } else {
            being_edited = { ...being_edited }; // should be cloned
        }
        const { left, top } = image_rect.current.getBoundingClientRect();
        const pos = e.type == 'touchstart' ? e.touches[0] : e;
        being_edited.start_x = pos.clientX - left;
        being_edited.start_y = pos.clientY - top;
        graphemes.update_fn(being_edited.idx, s => ({ ...s, box: [
            being_edited.start_x/image_width, being_edited.start_y/image_height,
            0,0] }), `GRAPH_${being_edited.idx}_UPD_BOX`);
        setEditing(being_edited);
        e.preventDefault();
        e.stopPropagation();
    };
    const rect_draw = e => {
        if (being_edited === null) return;
        if (being_edited.start_x === undefined) return;
        const { left, top } = image_rect.current.getBoundingClientRect();
        const pos = e.type == 'touchmove' ? e.touches[0] : e;
        const mx = pos.clientX - left;
        const my = pos.clientY - top;
        const bw = mx - being_edited.start_x;
        const bh = my - being_edited.start_y;
        graphemes.update_fn(being_edited.idx, s => ({ ...s, box: [
            (being_edited.start_x + bw/2)/image_width, // x
            (being_edited.start_y + bh/2)/image_height, // y
            (bw>=0?bw:-bw)/image_width, // w
            (bh>=0?bh:-bh)/image_height, // h
        ] }), `GRAPH_${being_edited.idx}_UPD_BOX`);
        e.preventDefault();
    }
    const start_edge_draw = (e, i) => {
        setEditing({
            start: i,
            start_x: graphemes.list[i].box[0] * image_width,
            start_y: graphemes.list[i].box[1] * image_height,
        });
        e.stopPropagation();
        e.preventDefault();
    };
    const edge_draw = e => {
        if (being_edited === null) return;
        const { left, top } = image_rect.current.getBoundingClientRect();
        const pos = e.type == 'touchmove' ? e.touches[0] : e;
        const mx = pos.clientX - left;
        const my = pos.clientY - top;
        setEditing(s => ({ ...s, 
            end_x: mx, end_y: my }));
        e.stopPropagation();
        e.preventDefault();
    };
    const edge_finish = (e, i) => {
        if (being_edited === null) return;
        if (being_edited.end_x === undefined) return;
        addEdge(being_edited.start, i);
        e.stopPropagation();
        e.preventDefault();
    };

    const mouse_down = mode == 'draw' ? start_rect_draw : null;
    const mouse_move = mode == 'draw' ? rect_draw : mode == 'edges' ? edge_draw : null;

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
                current=${being_edited && being_edited.idx==i}
                click=${mode=='select'?() => setEditing({ idx: i }):null}
                mousedown=${mode=='edges'?e => start_edge_draw(e, i):null}
                mousemove=${mouse_move}
                mouseup=${mode=='edges' && being_edited!==null ? 
                    e => edge_finish(e, i):null}
        />`)}
        ${edges.list.map(e => html`<${Edge}
            x1=${graphemes.list[e.start].box[0]*image_width}
            y1=${graphemes.list[e.start].box[1]*image_height}
            x2=${graphemes.list[e.end].box[0]*image_width}
            y2=${graphemes.list[e.end].box[1]*image_height}
            color=${colors.list[e.start]} />`)}
        ${being_edited && being_edited.end_x !== undefined ?
            html`<${Edge}
                x1=${being_edited.start_x} y1=${being_edited.start_y}
                x2=${being_edited.end_x} y2=${being_edited.end_y}
                color=${colors.list[being_edited.start]}
            />`:null}
    </div>`;
}

function BBox ({ x, y, w, h, color, image_width, image_height, current,
        click, mousemove, mousedown, mouseup }) {

    if (x === undefined) return null;
    const left = Math.round((x-w/2.0)*image_width)+'px';
    const top = Math.round((y-h/2.0)*image_height)+'px';
    const width = Math.round(w*1.0*image_width)+'px';
    const height = Math.round(h*1.0*image_height)+'px';

    const can_click = (click !== null) && !current;
    const do_click = e => {
        if (can_click) click();
        e.stopPropagation();
    };
    const interactive = can_click || mousemove !== null;

    return html`<span class=${`BBox ${current?'editing':''}`} style=${`
        left: ${left}; top: ${top};
        width: ${width}; height: ${height};
        border-color: ${color};
        cursor: ${interactive?'pointer':'default'};
        pointer-events: ${interactive?'auto':'none'};
        `}
        onclick=${do_click} onmousedown=${mousedown} onmouseup=${mouseup}
        onmousemove=${mousemove}
    />`;
}

const EDGE_MARGIN = 10;
function Edge ({ x1, y1, x2, y2, color }) {
    const left = (x1>x2 ? x2 : x1)-EDGE_MARGIN;
    const top = (y1>y2 ? y2 : y1)-EDGE_MARGIN;
    const width = Math.abs(x1-x2)+2*EDGE_MARGIN;
    const height = Math.abs(y1-y2)+2*EDGE_MARGIN;
    const markerId = `arrow-${color}`;
    return html`<svg viewBox=${`${left} ${top} ${width} ${height}`}
        style=${`position: absolute;
            left: ${left}px; top: ${top}px;
            width: ${width}px; height: ${height}px;
            pointer-events: none;
        `}>
        <defs>
            <marker id=${markerId} viewBox="0 0 10 10" refX="5" refY="5"
                markerWidth="8" markerHeight="8"
                orient="auto-start-reverse">
                <path d="M 0 0 L 10 5 L 0 10 z" fill=${color} />
            </marker>
        </defs>
        <line x1=${x1} y1=${y1}
            x2=${x2} y2=${y2}
            stroke=${color} stroke-width="2"
            vector-effect='non-scaling-stroke' marker-end='url(#${markerId})' />
    </svg>`;
}

function TagTable ({ g_tags, graphemes, colors, editing_grapheme, setEditing,
        removeGrapheme }) {
    return html`<div><table>
        <thead><tr><th />
            ${g_tags.map(c => html`<th>${c}</th>`)}
            <th />
        </tr></thead>
        <tbody>${graphemes.list.map((s, i) => {
            const current = editing_grapheme !== null && editing_grapheme.idx === i;
            return html`<${GraphemeEntry} tags=${s.tags || {}}
                changeTag=${(k, v) => graphemes.update_fn(i,
                        s => ({ ...s, tags: {...s.tags, [k]: v}}),
                        `GRAPH_${i}_UPD_TAG_${k}`)}
                columns=${g_tags}
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
    </table></div>`;
}

function GraphemeEntry ({ tags, changeTag, columns, remove,
        color, changeColor, markEditing, editing, navigate }) {
    return html`<tr class=${`GraphemeEntry ${editing?'editing':''}`}
        onmousedown=${markEditing} onclick=${markEditing}>
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
