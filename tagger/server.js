import express from 'express';
import { spawn } from 'child_process';
import fs from 'fs-extra';
import yaml from 'js-yaml';

const app = express();

app.set('views', '.');
app.set('view engine', 'ejs');
app.use(express.json());

let trans_list;
let last_id;
let data_dir;
let info;

async function load_list (dir) {
    info = yaml.safeLoad(await fs.readFile(`${dir}/info.yaml`));
    data_dir = `${dir}/real`;
    const files = await fs.readdir(data_dir);
    const ids = files
        .filter(file => file.endsWith('.png'))
        .map(file => file.slice(0, file.length-4))
        .sort((a,b)=>a-b);
    last_id = ids[ids.length-1];
    trans_list = await Promise.all(ids.map(async id => {
        const data = await fs.readJson(`${data_dir}/${id}.json`);
        return { id, annotated: data.symbols.length>0, meanings: data.meanings };
    }));
}

app.get('/', (req, res, next) => res.render('lista', { info, trans: trans_list }));

app.get('/edit/:id', (req, res, next) => {
    const id = req.params.id;
    fs.readJson(`${data_dir}/${id}.json`)
        .then(info => res.render('edit', {
            id,
            prev_link:`/edit/${+id>1?id-1:last_id}`,
            next_link: `/edit/${+id<last_id?+id+1:1}`,
            ...info }))
        .catch(next);
});

app.post('/edit/:id', (req, res, next) => {
    const info_file = `${data_dir}/${req.params.id}.json`;
    fs.readJson(info_file)
        .then(info => ({ ...info, ...req.body }))
        .then(new_info => fs.writeJson(info_file, new_info))
        .then(() => res.send('ok'))
        .catch(next);
});

app.get('/img/:img', (req, res) => res.sendFile(req.params.img, { root: data_dir }));

console.log("Loading dataset...");

load_list(process.argv[2]).then(() => {
    app.listen(3000, () => {
        console.log(`App started at http://localhost:3000`);
        spawn('firefox', [ 'http://localhost:3000' ]);
    });
}).catch(e => console.log(`Error: ${e}`));
