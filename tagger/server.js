import express from 'express';
import { spawn } from 'child_process';
import fs from 'fs-extra';

const data_dir = '../data/jmb22/real';

const app = express();

const makeAsync = fn => (req, res, next) => {
    Promise.resolve(fn(req, res, next)).catch(next);
};

app.get('/', makeAsync(async (req, res) => {
    const ids = await fs.readdir(data_dir)
        .then(files => files.filter(file => file.endsWith('.png')))
        .then(files => files.map(file => file.slice(0, file.length-4)));
    const trans = await Promise.all(ids.map(async id => {
        const data = await fs.readJson(`${data_dir}/${id}.json`);
        return { id, meaning: data.meanings[0] };
    }));
    res.send(`<!doctype html>
        <html>
        <head>
            <style>img { width: 200px; }</style>
        </head>
        <body>
            <ul>`+
        trans.map(({ id, meaning }) =>
            `<li>${id}: ${meaning}<img src="img/${id}.png" /></li>`)
            .join('')
        +`  </ul>
        </body>
        </html>
    `);
}));

app.get('/img/:img', (req, res) => {
    res.sendFile(req.params.img, { root: data_dir });
});

app.listen(3000, () => {
    console.log(`App started at http://localhost:3000`);
    spawn('firefox', [ 'http://localhost:3000' ]);
});
