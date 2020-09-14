- Remember: images need to be 3 channel

# Right now
Migrate tagger web app to preact instead of SSR flask html + spaguetti JS, in
order to be ablo to do annotation tables in a sane way.

# TODO

- Annotation tables
- Document dataset/annotation format !IMPORTANT
- Add option to change detection threshold in test and compare
- Use alexnet for symbols
- Check that letterboxing is working with AlexeyAB's darknet, and try again
  grayscale images
- Include improve.sh as python code (PIL) so that it can be used for test etc.
- Maybe move all hardcoded paths in the dataset to the Dataset class as properties.
- Use bash complete https://click.palletsprojects.com/en/7.x/bashcomplete/
