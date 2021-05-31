# Quevedo as a library

Quevedo can be used as a command line application to manage a dataset, but it
can also be used from other Python code to make programatic access to the
dataset more convenient, or in user scripts run by Quevedo on the dataset
objects.

## Call from python

To use Quevedo from other python code, you can import it with `import quevedo`,
or it may be more useful to directly import the Dataset class:
`from quevedo import Dataset`. This class has most of the functionality to deal
with Quevedo datasets, including managing the data and the neural networks.
There are some examples of use in the [examples
directory](https://github.com/agarsev/quevedo/tree/master/examples) of the repo,
and we try to keep the code readable to help understand the library. The full
API reference with the different classess and methods can be read [here](api.md).

## User scripts

Every dataset is different, and dealing with data often needs to have custom
procedures and algorithms, specific to the problem at hand. We suggest to place
these scripts in the `scripts` directory of the dataset, to keep them organized.
Quevedo can also help run scripts in this directory using the command
[`run_script`](cli.md#run_script).

With `run_script`, you don't need to write the boilerplate code of accessing all
the annotations, loading their data and image, and saving them. Just provide a
`process` function, which receives an annotation object and the dataset, and
process the annotation with your custom logic. The `run_script` command then
lets you specify, using syntax similar to the other commands, what subsets to
run the script in.

For example:

```
from datetime import date
from quevedo import Annotation, Dataset


# Our custom logic to get tags from the filename
def tags_from_filename(filename: str):
    tags = filename.split('_')
    if tags[0] == 'something':
        tags[0] = 'some other thing'
    return tags


def process(a: Annotation, ds: Dataset):

    if a.meta['author'] is not None:
        return False  # We don't want to modify this annotation

    a.meta['annotation_date'] = date.today()
    a.meta['author'] = 'automatic'

    # The original filename is kept by `add_images`
    a.tags = tags_from_filename(a.meta['filename'])

    # We have updated the annotation, so return True for Quevedo to save it
    return True
```

Another advantage of user scripts is that Quevedo makes them available on the
[web interface](web_use.md#user-scripts). The top right corner of the annotation
page has a listing of functions, including trained neural networks and user
scripts, that can be run, allowing annotators to access this functionality
directly from the web interface. If the script is used from the web interface,
the annotation won't be automatically saved, allowing the user to review the
results before clicking save.

## Modifying Quevedo

Quevedo is open source! You can modify and extend it by [forking it on
GitHub](https://github.com/agarsev/quevedo). If you use Quevedo for your
research and have ideas for improvement, please do get in touch via GitHub
discussions or email.
