import express from 'express';
import { spawn } from 'child_process';
import fs from 'fs-extra';
import yaml from 'js-yaml';

const app = express();

app.set('views', '.');
app.set('view engine', 'ejs');
app.use(express.json());

let config = {};

function annotated_status (d) {
    return d.symbols.length>0;
}

async function load_dataset (dir) {
    config.path = await fs.realpath(dir);
    config.data_dir = `${dir}/real`;
    config.info = yaml.safeLoad(await fs.readFile(`${dir}/info.yaml`));
    const files = await fs.readdir(config.data_dir);
    const ids = files
        .filter(file => file.endsWith('.png'))
        .map(file => file.slice(0, file.length-4))
        .sort((a,b)=>a-b);
    config.last_id = ids[ids.length-1];
    config.trans = await Promise.all(ids.map(async id => {
        const data = await fs.readJson(`${config.data_dir}/${id}.json`);
        return { id, annotated: annotated_status(data), meanings: data.meanings };
    }));
}

app.get('/', (req, res, next) => res.render('lista', config));

app.get('/edit/:id', (req, res, next) => {
    const id = req.params.id;
    fs.readJson(`${config.data_dir}/${id}.json`)
        .then(annotation => res.render('edit', {
            id,
            prev_link:`/edit/${+id>1?id-1:config.last_id}`,
            next_link: `/edit/${+id<config.last_id?+id+1:1}`,
            info: config.info,
            ...annotation }))
        .catch(next);
});

app.post('/edit/:id', (req, res, next) => {
    const info_file = `${config.data_dir}/${req.params.id}.json`;
    fs.readJson(info_file)
        .then(info => {
            const new_info = { ...info, ...req.body };
            config.trans.find(el => el.id==req.params.id)
                .annotated = annotated_status(new_info);
            return fs.writeJson(info_file, new_info);
        })
        .then(() => res.sendStatus(200))
        .catch(next);
});

app.get('/img/:img', (req, res) => res.sendFile(req.params.img, { root: config.data_dir }));

console.log("Loading dataset...");

load_dataset(process.argv[2]).then(() => {
    app.listen(3000, () => {
        console.log(`Tagger started at http://localhost:3000`);
    });
}).catch(e => console.error(`Error: ${e}`));
