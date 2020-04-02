import express from 'express';
import { spawn } from 'child_process';
import fs from 'fs-extra';

const data_dir = '../data/jmb22/real';

const app = express();

app.set('views', '.');
app.set('view engine', 'ejs');

async function list_trans (dir) {
    const files = await fs.readdir(dir);
    const ids = files
        .filter(file => file.endsWith('.png'))
        .map(file => file.slice(0, file.length-4));
    return await Promise.all(ids.map(async id => {
        const data = await fs.readJson(`${data_dir}/${id}.json`);
        return { id, meanings: data.meanings };
    }));
}

app.get('/', (req, res, next) => {
    list_trans(data_dir)
        .then(trans => res.render('lista', { trans }))
        .catch(next);
});

app.get('/img/:img', (req, res) => res.sendFile(req.params.img, { root: data_dir }));

app.listen(3000, () => {
    console.log(`App started at http://localhost:3000`);
    spawn('firefox', [ 'http://localhost:3000' ]);
});
