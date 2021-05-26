# Web Interface

The data that Quevedo aims to manage are highly visual, and therefore a visual
interface can be very useful. Indeed, in the case of annotation, being able to
see the target of annotation is fundamental. It is also a task which may
be shared between a team, or conducted by people who are not data scientists or
engineers and don't feel comfortable with code and a command line interface.

Quevedo provides a web interface which can be used to visualize, manage and
annotate data in a Quevedo dataset. The web interface has the advantage that is
graphical, and it can also be run on a server or some shared computer accesible
via the internet so that collaborators can work on the dataset without any
infrastructure needs on their part (beyond a modern browser).

To use the web interface locally, just run `quevedo web`. This will launch the
server in a local port and open a browser window at the appropriate location. To
quit the server, just press `Ctrl+C` in the terminal window. For more options
see the rest of this document, and for usage of the web interface see
[here](web_use.md).

!!! note
    The web interface for Quevedo is not intended to be used as a permanent,
    production website, but rather to provide access to collaborators during a
    project.

## Configuration

Some options for the web interface can be configured in the [dataset
configuration file](config.md). Since some of these settings may be sensitive,
they can be set in the local configuration file if the dataset is going to be
distributed publicly.

The main configuration is set under the heading `web`, and the following options
can be set:

## Server options

- `host`, `port`: IP address and port to bind the server to.
- `mount_path`: path under which the application will be mounted.
- `secret_key`: secret string to sign session cookies. You can generate a random
    one for your installation with
    `python -c 'from secrets import token_hex; print(token_hex(16))'`.

## Interface options

- `lang`: the language for messages in the web interface. Supported values for
    now are `en` (english) or `es` (spanish).
- `public`: If true, no login will be required. If false, access will only be
    provided to logged in users.

## Users

To create a user (needed if the dataset interface is not set to `public`) add a
heading `[web.users.<user_name>]`, with the following options:

- `password`: hex digest of the sha1 hash of the password for the user. You can
    generate the hash with the following code:
    `python -c 'import hashlib; print(hashlib.new("sha1", "thepassword".encode("utf8")).hexdigest());'`.
- `read`: subsets that the user has *read* access to. Can be `ALL`, `NONE`, or a
    list of subsets to allow access to. These strings are actually
    [regexes][regex], so any subset matching them will be available.
- `write`: subsets that the user has *write* access to. Follows the same syntax
    of `read`. Write access means adding annotations to a subset, and *saving*
    modified annotations to the server (the annotation can be changed locally,
    but not saved).

Assuming we have the sets `spanish_a`, `spanish_b` and `english_a`:

- `read = [ "spanish", "english" ]` will allow access to all sets.
- `read = [ "spanish_a" ]` will only allow access to the `spanish_a` set.
- `read = [ "_a" ]` will allow access to the `spanish_a` and `english_a` sets.

You can use `^`, `$`, and other [regex] syntax to be more specific.

!!! warning
    This system of managing users is not very sophisticated, intended to prevent
    mistakes or unintentional leaks of data rather than actual security. Please
    don't put here your email or bank passwords, nor ask your collaborators to
    provide them to you.

[regex]: https://docs.python.org/3/library/re.html#regular-expression-syntax
