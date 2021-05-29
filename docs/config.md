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
configuration file override those in the main file.

This can be useful for the configuration of darknet installation, which is
likely different for different environments, and for the web interface, which
may contain sensitive information like secrets and users' passwords (even if
hashed).

## Annotation schema

Two important options in the configuration file are `tag_schema` and
`meta_tags`. These describe the schema of the dataset annotation, and are a list
of strings with the names of the different tags.

The `meta_tags` are used to add information to each annotation file, such as
filename, author of the annotation, but also maybe meaning of the transcription,
etc. They are common to both logograms and graphemes. They are stored as a
dictionary in the annotation file and the annotation objects in the code.

The `tag_schema` is a list of the different tags that each grapheme, either
isolated or bound, can have. The tags are then stored as lists themselves both
in the files and the code.  Therefore, if the tag schema of a dataset is
`tag_schema = [ "COARSE", "FINE" ]`, and a grapheme has
`tags = [ "symbol", "character" ]` this means that for this grapheme, the
`COARSE` tag has value `symbol`, and the `FINE` tag has value `character`.

Isolated graphemes (in the `graphemes` directory) have a single list of tags
associated with the transcription. Conversely, logograms have a list of
graphemes that can be found in them. This list includes the grapheme position,
and also the tag list in the same format and with the same meaning as for
isolated graphemes.

## Other options

- `darknet`: Configuration for using the darknet binary and library. See
    [`Darknet installation`](nets.md#installation).
- `network`: Configuration for training and using neural networks. See
    [`Network configuration`](nets.md#network-configuration).
- `web`: Configuration for the web interface. See
    [`Web interface configuration`](web.md#configuration).
- `generate`: These options guide the process of artificial logogram generation
    used for data augmentation. See [`generate`](cli.md#generate).

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

annotation_help = """
Write here any help for annotators, like lists of graphemes or other
instructions. For example:

Make boxes slightly larger than the graphemes, not too tight.
"""

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
