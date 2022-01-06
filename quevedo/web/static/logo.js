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

const ANNOT_OPTIONS = [
    { value: 'hide', label: Text['hide'] },
    { value: 'show', label: Text['show'] },
    { value: 'draw', label: Text['draw'] },
];
const TAG_OPTIONS = [
    { value: 'graphemes', label: Text['graphemes'] },
    { value: 'edges', label: Text['edges'] },
    { value: 'both', label: Text['graph_and_edges'] },
];

export function LogogramEditor ({ id, graphemes, edges, g_tags, e_tags,
    color_list, changes }) {

    // ANNOT_OPTIONS
    const [ box_mode, _setBoxMode ] = useSavedState('show_boxes', 'show');
    const [ edge_mode, _setEdgeMode ] = useSavedState('show_edges', 'show');
    const [ tag_mode, _setTagMode ] = useSavedState('show_tags', 'graphemes');

    function setBoxMode (mode) {
        _setBoxMode(mode);
        if (mode === 'draw') {
            if (edge_mode === 'draw') _setEdgeMode('show');
            if (tag_mode == 'edges') _setTagMode('graphemes');
        }
    }
    function setEdgeMode (mode) {
        _setEdgeMode(mode);
        if (mode === 'draw') {
            if (box_mode === 'draw') _setBoxMode('show');
            if (tag_mode == 'graphemes') _setTagMode('edges');
        }
    }
    function setTagMode (mode) {
        _setTagMode(mode);
        if (mode === 'edges' && box_mode === 'draw') _setBoxMode('show');
        if (mode === 'graphemes' && edge_mode === 'draw') _setEdgeMode('show');
    }

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
        if (box_mode == 'draw' || edge_mode == 'draw') {
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
    }, [box_mode, edge_mode]);

    const removeGrapheme = i => {
        const action = `GRAPH_RM_${Math.random()}`;
        setEditing(null);
        changes.push(() => {
            graphemes._set(graphemes.list);
            colors.set(colors.list);
            edges._set(edges.list);
        }, action);
        graphemes.remove(i, action);
        colors.remove(i);
        let el = edges.list.slice()
            .filter(e => e.start != i && e.end != i);
        for (let j = 0; j < el.length; j++) {
            let e = el[j];
            if (e.start > i) e = {...e, start: e.start-1};
            if (e.end > i) e = {...e, end: e.end-1};
            el[j] = e;
        }
        edges.set(el, action);
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

    return html`
        <h2 class="AnnotationHeader">${Text['annotation']}
            <${ModeSelect} value=${box_mode} label=${Text['boxes']} set=${setBoxMode} options=${ANNOT_OPTIONS} />
            <${ModeSelect} value=${edge_mode} label=${Text['edges']} set=${setEdgeMode} options=${ANNOT_OPTIONS} />
            <${ModeSelect} value=${tag_mode} label=${Text['tags']} set=${setTagMode} options=${TAG_OPTIONS} />
        </h2>
        <div class="GraphemeList">
        <${Annotation} ...${{id, graphemes, edges, colors, being_edited,
            setEditing, addEdge, box_mode, edge_mode }} />
        ${tag_mode!='edges' && html`<${TagTable} mode="graphemes"
            columns=${g_tags}
            objects=${graphemes}
            remove=${removeGrapheme}
            ...${{colors, being_edited, setEditing}} />`}
        ${tag_mode!='graphemes' && html`<${TagTable} mode="edges"
            columns=${e_tags}
            objects=${edges}
            remove=${i => edges.remove(i)}
            ...${{colors, being_edited, setEditing}} />`}
        </div>
    `;
}

function ModeSelect ({ value, label, set, options }) {
    return html`<label class="ModeSelect">
        ${label}: <select value=${value} onchange=${e => {
            set(e.target.value);
            e.stopPropagation();
        }}>
        ${options.map(({ value, label }) => html`<option value=${value}>${label}</option>`)}
        </select>
    </label>`;
}

function Annotation ({ id, graphemes, edges, colors, being_edited, setEditing,
    addEdge, box_mode, edge_mode }) {

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

    const mouse_down = box_mode == 'draw' ? start_rect_draw : e => e.preventDefault();
    const mouse_move = box_mode == 'draw' ? rect_draw : 
                       edge_mode == 'draw' ? edge_draw : null;

    return html`<div class="Annotation">
        <img src="img/${id.full}.png"
            ref=${image_rect}
            onmousedown=${mouse_down}
            onmousemove=${mouse_move}
            ontouchstart=${mouse_down}
            ontouchmove=${mouse_move}
        />
        ${(box_mode != 'hide' || edge_mode == 'draw') && graphemes.list.map((s, i) =>
            html`<${BBox}
                x=${s.box[0]} y=${s.box[1]}
                w=${s.box[2]} h=${s.box[3]}
                color=${box_mode != 'hide' ? colors.list[i] : 'transparent'}
                image_width=${image_width}
                image_height=${image_height}
                current=${being_edited && being_edited.idx==i}
                dim=${(being_edited?.idx != null && being_edited.idx!=i) ||
                      (being_edited?.ide != null && 
                       being_edited.start!=i && being_edited.end!=i)}
                click=${(box_mode=='show' && edge_mode!='draw')?
                        () => setEditing({ idx: i }):null}
                mousedown=${edge_mode=='draw'?e => start_edge_draw(e, i):null}
                mousemove=${mouse_move}
                mouseup=${edge_mode=='draw' && being_edited!==null ? 
                    e => edge_finish(e, i):null}
        />`)}
        ${edge_mode != 'hide' && edges.list.map((e, i) => html`<${Edge}
            x1=${graphemes.list[e.start].box[0]*image_width}
            y1=${graphemes.list[e.start].box[1]*image_height}
            x2=${graphemes.list[e.end].box[0]*image_width}
            y2=${graphemes.list[e.end].box[1]*image_height}
            color=${colors.list[e.start]}
            highlight=${being_edited && (being_edited.idx==e.start || being_edited.idx==e.end)}
            dim=${(being_edited?.ide != null && being_edited.ide!=i) ||
                  (being_edited?.idx != null &&
                   e.start!=being_edited.idx && e.end!=being_edited.idx)}
        />`)}
        ${being_edited && being_edited.end_x !== undefined ?
            html`<${Edge} drawing=${true}
                x1=${being_edited.start_x} y1=${being_edited.start_y}
                x2=${being_edited.end_x} y2=${being_edited.end_y}
                color=${colors.list[being_edited.start]}
            />`:null}
    </div>`;
}

function BBox ({ x, y, w, h, color, image_width, image_height, dim,
        click, mousemove, mousedown, mouseup }) {

    if (x === undefined) return null;
    const left = Math.round((x-w/2.0)*image_width)+'px';
    const top = Math.round((y-h/2.0)*image_height)+'px';
    const width = Math.round(w*1.0*image_width)+'px';
    const height = Math.round(h*1.0*image_height)+'px';

    const can_click = click !== null;
    const do_click = e => {
        if (can_click) click();
        e.stopPropagation();
    };
    const interactive = can_click || mousedown !== null;

    return html`<span class=${`BBox ${dim?'dim':''}`} style=${`
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
const SHORTEN_PERCENT = 0.15;
const MAX_SHORTEN_LENGTH = 20;
function Edge ({ x1, y1, x2, y2, color, drawing, dim }) {
    const left = (x1>x2 ? x2 : x1)-EDGE_MARGIN;
    const top = (y1>y2 ? y2 : y1)-EDGE_MARGIN;
    const width = Math.abs(x1-x2)+2*EDGE_MARGIN;
    const height = Math.abs(y1-y2)+2*EDGE_MARGIN;
    const markerId = `arrow-${color}`;
    // Shorten the arrow a bit
    let shorten_x = (x2-x1) * SHORTEN_PERCENT;
    if (shorten_x > MAX_SHORTEN_LENGTH) shorten_x = MAX_SHORTEN_LENGTH;
    if (shorten_x < -MAX_SHORTEN_LENGTH) shorten_x = -MAX_SHORTEN_LENGTH;
    let shorten_y = (y2-y1) * SHORTEN_PERCENT;
    if (shorten_y > MAX_SHORTEN_LENGTH) shorten_y = MAX_SHORTEN_LENGTH;
    if (shorten_y < -MAX_SHORTEN_LENGTH) shorten_y = -MAX_SHORTEN_LENGTH;
    const start_x = x1 + shorten_x;
    const start_y = y1 + shorten_y;
    const end_x = x2 - (drawing?0:shorten_x);
    const end_y = y2 - (drawing?0:shorten_y);

    return html`<svg viewBox=${`${left} ${top} ${width} ${height}`}
        class="Edge ${dim?'dim':''}"
        style=${`left: ${left}px; top: ${top}px;
            width: ${width}px; height: ${height}px;
            pointer-events: none;
            color: ${color};
        `}>
        <defs>
            <marker id=${markerId} viewBox="0 0 10 10" refX="5" refY="5"
                markerWidth="8" markerHeight="8"
                orient="auto-start-reverse">
                <path d="M 0 0 L 10 5 L 0 10 z" fill=${color} />
            </marker>
        </defs>
        <line x1=${start_x} y1=${start_y} x2=${end_x} y2=${end_y}
            stroke=${color}
            vector-effect='non-scaling-stroke' marker-end='url(#${markerId})' />
    </svg>`;
}

function TagTable ({ mode, columns, objects, colors, being_edited, setEditing, remove }) {
    const markEditing = mode == 'graphemes'?
        (idx) => setEditing({ idx }):
        (ide) => setEditing({ ide,
            start: objects.list[ide].start,
            end: objects.list[ide].end });
    return html`<div><table>
        <thead><tr><th />
            ${columns.map(c => html`<th>${c}</th>`)}
            <th />
        </tr></thead>
        <tbody>${objects.list.map((s, i) => {
            let highlight = '';
            if (mode == 'graphemes' && being_edited?.idx == i) {
                highlight = 'editing';
            } else if (mode == 'edges' && being_edited?.ide == i) {
                highlight = 'editing';
            } else if (mode == 'edges' && (being_edited?.idx == s.start || being_edited?.idx == s.end)) {
                highlight = 'related';
            } else if (mode == 'graphemes' && (being_edited?.start == i || being_edited?.end == i)) {
                highlight = 'related';
            }
            return html`<${GraphemeEntry} tags=${s.tags || {}}
                changeTag=${(k, v) => objects.update_fn(i,
                        s => ({ ...s, tags: {...s.tags, [k]: v}}),
                        `${mode}_${i}_UPD_TAG_${k}`)}
                columns=${columns}
                colors=${colors}
                color1=${mode=='graphemes'?i:s.start}
                color2=${mode=='edges'?s.end:null}
                remove=${() => remove(i)}
                markEditing=${e => { markEditing(i); e.stopPropagation(); }}
                highlight=${highlight}
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
        colors, color1, color2, markEditing, highlight, navigate }) {
    return html`<tr class=${`GraphemeEntry ${highlight}`}
        onclick=${markEditing}>
        <td>
            <input type=color value=${colors.list[color1]}
                oninput=${e => colors.update(color1, e.target.value)} />
            ${color2!==null?html`<input type=color value=${colors.list[color2]}
                oninput=${e => colors.update(color2, e.target.value)} />`:''}
        </td>
        ${columns.map(c => html`<td><input type=text
            placeholder=${c} tabIndex=1 value=${tags[c] || ''}
            oninput=${e => changeTag(c, e.target.value)}
            onkeydown=${navigate}
            onfocus=${markEditing} /></td>`)}
        <td><button onclick=${e => {remove(); e.stopPropagation();}}>🗑️</button></td>
    </tr>`;
}
