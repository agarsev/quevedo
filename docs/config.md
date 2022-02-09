# Dataset Configuration

All configuration of a Quevedo dataset is found in its configuration file, which
is found at the root of the dataset and named `config.toml`. This file is in
[TOML] format, which makes it ideal for both human and machine editing. We
recommend reading TOML documentation to really understand the format, but it is
an intuitive enough language that you can understand the configuration file
enough to modify it just by reading it.

As a convenience, quevedo provides the [`quevedo config`](cli.md#config) command
to edit the configuration file, but this only launches the user's configured
text editor with the `config.toml` file open.

## Local configuration

Quevedo datasets are meant to be shared, and configuration is an essential part
of the dataset. However, some options may be applicable only for the local
environment, and others may be sensitive and best not distributed. For this,
Quevedo also reads a `config.local.toml` if present. The options in the local
configuration file are merged with those in the main file, overriding them when
there is a conflict.

This can be useful for the configuration of darknet installation, which is
likely different for different environments, and for the web interface, which
may contain sensitive information like secrets and users' passwords (even if
hashed).

## Annotation schema

The annotation schema of a dataset is a complex set of information and
decisions, but to Quevedo, the important information is the featuers that
graphemes, logograms and edges can have. These are lists of strings, and each
string represents a possible feature for an annotation object. Each concrete
object, then, has a particular value (another string) for each of the
appropriate features in its schema. There are four schemas:

- `g_tags`: Possible features for each grapheme, either bound or isolated.
- `l_tags`: Features for each of the logograms.
- `e_tags`: Features for the edges of the logogram graph.
- `meta_tags`: Additional information that can be stored for isolated annotation
    files, either graphemes or logograms, but not for bound graphemes.

Tags are represented as dictionary objects both in the annotation files (in
`json` format) and in the code (python `dict`s).

!!! warning
    In versions of Quevedo before v1.1, tags were stored as a list instead of
    a dictionary. Before v1.3, there was no logogram annotation schema. If your
    dataset is using an old structure, Quevedo will warn you. Please run the
    [`migrate`](cli.md#migrate) command to upgrade the dataset.

In the annotation file, apart from their own `tags`, logograms have a list of
graphemes found within them. These bound graphemes have their own `tags` from
the `g_tags` schema, and an additional piece of information: the coordinates
where they can be found within the logogram image (a.k.a bounding boxes).

## Other options

- `darknet`: Configuration for using the darknet binary and library. See
    [`Darknet installation`](nets.md#installation).
- `network`: Configuration for training and using neural networks. See
    [`Network configuration`](nets.md#network-configuration).
- `pipeline`: Configuration for pipelines which use many networks to solve
    a task. See [`Pipeline configuration`](pipes.md#pipeline-configuration).
- `web`: Configuration for the web interface. See
    [`Web interface configuration`](web.md#configuration).
- `generate`: These options guide the process of artificial logogram generation
    used for data augmentation. See [`generate`](cli.md#generate).
- `folds`, `train_folds`, `test_folds`: The `folds` option sets the default
    folds that the [`split`](cli.md#split) will use to partition annotations.
    The `train_folds` option is a list of fold values that will be used to
    train, and the `test_folds` option respectively for testing.
    See [`Splits and folds`](guide.md#splits-and-folds) for more.

## Default configuration

When creating a dataset, Quevedo places a default configuration file with
comments to ease personalization. The default file is included here for
reference:

```toml
# This file is a Quevedo dataset configuration file. Find more at:
# https://www.github.com/agarsev/quevedo

# Local overrides can be written in `config.local.toml`

title = "The title"

description = """ 
The dataset description.
"""

tag_schema = [ "tag" ]
# For a multi-tag schema, use:
# tag_schema = [ "tag1", "tag2" ]

# Meta tags affect the whole annotation, rather than individual graphemes. The
# first one will be used as title for the annotation in the web listing.
meta_tags = [ "filename", "meaning" ]

# Flags are also meta tags, but can only be true/false. They are displayed in
# the web interface as checkboxes with the icon set here.
flags = { done = "✔️", problem = "⚠️", notes = "📝" }

annotation_help = """
Write here any help for annotators, like lists of graphemes or other
instructions. For example:

Make boxes slightly larger than the graphemes, not too tight.
"""

config_version = 1 # Version of quevedo dataset schema, not of dataset data

# Number of folds to split annotations into, and which to use for training and
# which to use for testing
folds = 10
train_folds = [0,1,2,3,4,5,6,7]
test_folds = [8,9]

[darknet]
path = "darknet/darknet" 
library = "darknet/libdarknet.so"
options = [ "-dont_show", "-mjpeg_port", "8090" ]

[network.one]
default = true # Network to use if not specified
task = "detect"
# tag = "tag" # Uncomment and choose a tag name from tag_schema to use
# subsets = [ "default" ] # If not specified, all subsets will be used
subject = "Focus on grapheme type learning and recognition"

[network.two]
task = "classify"
# tag = "tag"
# tag = [ "tag1", "tag2" ] # A combination of tags can be used as the network "class"
subsets = [ "default" ]
subject = "Classify graphemes"

# A filter can be used to select the annotations to use for training this network
# [network.two.filter]
# criterion = "tag"  # Tag to use to decide whether to include or not each annotation
# include = [ "value" ]  # Values for the criterion to use
# # exclude = [ "value" ]  # Alternatively, values to exclude

# Automatic data augmentation can be configured here:
# [network.two.augment]
# angle = 10
# flip = 1  # yes/no, 1/0
# exposure = 0.8
# aspect = 0.8  # only for classify tasks

# Add more networks like so:
# [network.other]
# task = "detect" or "classify"
# tag = "tag"
# subject = "human readable description"
# ...

[web]
host = "localhost"
port = "5000"
mount_path = ""
lang = "en"
public = true # Set to false to require login
# Generate your own secret key with, for example: 
#   python -c 'from secrets import token_hex; print(token_hex(16))'
secret_key = "ce8c9cd0316faac773645648ac827ff6"

# [web.users.annotator]
# # Uncomment and modify to add users
# # Hash the password with:
# #     python -c 'import hashlib; print(hashlib.new("sha1", "thepassword".encode("utf8")).hexdigest());'
# password = ""
# read = "ALL" # Can read all subsets
# # read = [ "public" ] # Can read all subsets that contain the string 'public'
# write = "NONE" # Can't write (modify) any subsets
# # write = [ "set1$$", "set2$$" ] # Can write to set1 and set2, both logogram or
#                                  # graphemes (they are regexes)
#
# [web.users.user2]
# ...

[generate]
# Configuration for the artificial logogram generation
count = 500
width_range = [ 200, 300 ]
height_range = [ 200, 300 ]
tag = "tag" # Tag to guide grapheme placement

[[generate.params]]
match = 'one' # Match graphemes tagged with class "one"
mode = 'one' # Only put one of these graphemes
freq = 0.4 # How often to add one of these
rotate = false

[[generate.params]]
match = 'excluded'
mode = 'none' # Don't put any of these graphemes

[[generate.params]]
match = '.*' # Match any grapheme (it's a regex)
mode = 'many' # Add potentially many of these graphemes
max = 3 # How many to potentially add
prob = 0.6 # Probability for a single grapheme to appear (times max = expected number)
rotate = true
```


[TOML]: https://toml.io/en/
