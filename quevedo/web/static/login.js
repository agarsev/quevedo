// 2021-03-03 Antonio F. G. Sevilla <afgs@ucm.es>
// Licensed under the Open Software License version 3.0

import Text from './i18n.js';

const html = htm.bind(preact.h);
const { useState, useRef } = preactHooks;

preact.render(html`<${App} ...${window.quevedo_data} />`, document.body);

function App () {

    /* 0: none, 1: sent, 2: errored */
    const [ resp, setResp ] = useState(0);
    const user = useRef();
    const pass = useRef();
    const dologin = e => {
        setResp(1);
        fetch(`api/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            redirect: 'follow',
            body: JSON.stringify({
                user: user.current.value,
                pass: pass.current.value,
            })
        }).then(r => {
            if (r.ok) { window.location = r.url; }
            else { setResp(2); }
        });
        e.preventDefault();
    };
    
    return html`<form class="LoginBox" onsubmit=${dologin}>
        <label>
            <span>${Text['user']}:</span>
            <input ref=${user} type="text" />
        </label>
        <label>
            <span>${Text['pass']}:</span>
            <input ref=${pass} type="password" />
        </label>
        ${resp==2?html`<div class="error">${Text['wronglogin']}</div>`:
                resp==1?html`<div class="loading">${Text['loadlogin']}</div>`:
                null}
        <button>${Text['login']}</button>
    </form>`;
}
