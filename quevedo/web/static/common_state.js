// 2020-12-02 Antonio F. G. Sevilla <afgs@ucm.es>
// Licensed under the Open Software License version 3.0

const { useState, useEffect, useRef } = preactHooks;

function preventLostChanges (e) {
    e.preventDefault();
    e.returnValue = Text['warning_save'];
}

const MAX_UNDO_STEPS = 30;
export function useChangeStack () {

    /* Prevent loss of changes by unintentional page unloading:
     * 0: no changes/all changes saved
     * 1: changes done
     * 2: changes submitted to server
     */
    const [ dirty, setDirty ] = useState(0);
    useEffect(() => {
        if (dirty>0) {
            window.addEventListener('beforeunload', preventLostChanges);
            return () => window.removeEventListener('beforeunload', preventLostChanges);
        }
    }, [dirty]);

    /* Save last MAX_UNDO_STEPS to allow undo */
    const { current: stack } = useRef([]);
    const last_action = useRef(undefined);
    const [ some, setSome ] = useState(false);

    return { 
        dirty, setSaving: () => setDirty(2),
        setSaved: () => {
            setDirty(0);
            stack.forEach(step => step.dirty = 1);
        },
        some, // there are changes to undo
        push: (cb, action) => {
            /* cb is the "undoer" function that reverts the change, "action" is
             * a string that identifies the "logical" change so that many small
             * steps pertaining to the same real action can be undone together. */
            if (action != undefined && action == last_action.current) return;
            stack.push({ cb, dirty });
            setDirty(1);
            last_action.current = action;
            if (stack.length>MAX_UNDO_STEPS) {
                stack.shift();
            }
            setSome(true);
        },
        undo: () => {
            if (stack.length == 1) setSome(false);
            const { cb, dirty } = stack.pop();
            setDirty(dirty);
            cb();
            last_action.current = null;
        }
    };
}

export function useList (initial_value, change_stack) {
    const [ list, setList ] = useState(initial_value);
    const set = change_stack ?
        (l, action) => { 
            change_stack.push(() => setList(list), action);
            setList(l);
        } : setList;
    return { list, set, _set: setList,
        add: (v, action) => set(list.concat([v]), action),
        remove: (i, action) => {
            let nl = list.slice(); nl.splice(i, 1);
            set(nl, action);
        },
        update: (i, v, action) => {
            let nl = list.slice(); nl[i] = v;
            set(nl, action);
        },
        update_fn: (i, fn, action) => {
            let nl = list.slice(); nl[i] = fn(list[i]);
            set(nl, action);
        }
    };
}

export function useDict (initial_value, change_stack) {
    const [ dict, setDict ] = useState(initial_value);
    const set = (d, action) => {
        change_stack.push(() => setDict(dict), action);
        setDict(d);
    };
    return { dict, set,
        update: (k, v, action) => set({...dict, [k]: v}, action)
    };
}

export function useSavedState (name, default_value) {
    let saved;
    try {
        saved = JSON.parse(localStorage.getItem('quevedo.'+name));
    } catch {
        saved = localStorage.getItem('quevedo.'+name);
    }
    const [ state, setState ] = useState(saved || default_value);
    return [ state, v => {
        localStorage.setItem('quevedo.'+name, JSON.stringify(v));
        setState(v);
    } ];
}
