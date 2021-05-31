// 2021-03-22 Antonio F. G. Sevilla <afgs@ucm.es>
// Licensed under the Open Software License version 3.0

const html = htm.bind(preact.h);

import Text from './i18n.js';

export function GraphemeEditor ({ id, tags, columns }) {
    return html`
        <h2>${Text['grapheme_annotation']}</h2>
        <div class="GraphemeList">
            <div class="Annotation">
                <img src="img/${id.full}.png" />
            </div>
            <${TagEditor} ...${{tags, columns}} />
        </div>
    `;
}

function TagEditor ({ tags, columns }) {
    return html`<div><table><tbody>
        ${columns.map((c, i) => html`<tr>
            <th>${c}:</th>
            <td><input type=text
                value=${tags.list[i] || ''}
                oninput=${v => tags.update(i, 
                    v.target.value, `TAG_${i}_UPD`)}
            /></td>
        </tr>`)}
    </tbody></table></div>`
}