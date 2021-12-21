// 2021-03-22 Antonio F. G. Sevilla <afgs@ucm.es>
// Licensed under the Open Software License version 3.0

const html = htm.bind(preact.h);

import Text from './i18n.js';

export function GraphemeEditor ({ id }) {
    return html`
        <h2 class="AnnotationHeader">${Text['annotation']}</h2>
        <div class="GraphemeList">
            <div class="Annotation">
                <img src="img/${id.full}.png" />
            </div>
        </div>
    `;
}
