# Simpler Rsync

I'm unable to remember the `rsync` options I usually need for transferring files to a remote location. Also, I'm too lazy to memorize the remote path. So I made a wrapper around `rsync` which reads from a config file in the current directory.

## Getting Started

You can install Simpler Rsync either with `pip install` or manually. The former works great for me, but is not well tested beyond my OS X setups.

### With `pip`
This all-important one-liner should take care of pretty much everything:

```bash
pip install https://github.com/AndiH/simpler-rsync/archive/master.zip
```

You should have a command `sync.py` no available in your shell. In the process, all dependencies should be installed as well. (This is the first time I tried setuptools, so let me know if something is not working). 

More manually, you could clone into some temporary directory and call `pip` into that directory:

```bash
cd $TMPDIR
git clone https://github.com/AndiH/simpler-rsync.git
cd simpler-rsync
pip install .
```

### Without `pip`

```bash
cd ~/bin/
git clone https://github.com/AndiH/simpler-rsync.git
ln -s simpler-rsync/sync.py
sync.py --help
```

You should insert `~/bin/` into your `$PATH`, e.g. via `export PATH=$HOME/bin/:$PATH` so you can use `sync.py` globally from any folder. If `sync.py` does not run, make sure to have installed all [dependencies](#dependencies).

## Options
`sync.py` reads from a configuration file in the current directory. Depending on the parameters specified there, the content of the current directory is copied to a target location using `rsync`.

The Python script has a few command line options, all documented via `./sync.py --help`:

* **`ENTRY`**: The name of the entry in the config file to be used for synchronization. If not specified, the *default* entry is taken. If there's no default, the first entry is taken. Maybe, at least, since the read-in of the config file is not strongly controlled…
* **`--config_file=somefile`**: Specify a different config file. The default is `.sync.toml`.
* **`--dryrun`**: Calls `rsync` with `--dryrun`, preventing all actual copies. Good for testing.
* **`--verbose`**: Output every step and test of the script.
* **`--rsync_options="--something"`**: Propagate `--something` to `rsync` as an additional option. Can be invoked multiple times. Shorthand: `-o`. The `rsync` option is given in addition to the basic, default options hardcoded into the script file and in addition to the options defined in the config file.

To specify values for the options globally, environment values can be set. This is handy if you don't like my choice of calling the default config file `.sync.toml` (see below) and want to change it. The command line options (at least the last three from the list above) are accessible as environment variables with a `SRSYNC_` prefix, thanks to [Click](http://click.pocoo.org/). So, for example, to rename the default config file, do:

```bash
export SRSYNC_CONFIG_FILE=.my.toml
sync.py somehost
```

## Config File
The config file used for Simpler Rsync is written in [TOML](https://github.com/toml-lang/toml). One entry in the config file is for one distinct parameter configuration, i.e. usually for one remote location. The config file is structured as follows.

```toml
[firsthost]
    hostname = "first"
    target_folder = "/something/"
    rsync_options = ["--delete", "-v"]

[secondhost]
    hostname = "127.0.0.1"
    target_folder = "/something/"
    default = true
```

The available keys are:

* **`hostname`**: A hostname to be understood by `rsync`. Hint: Use aliases in your `~/.ssh/config/`!
* **`target_folder`**: The target directory to be syncing to (remote or local).
* **`rsync_options`**: A array of strings of `rsync` options. They are used in addition to the default, basic options hardcoded into the Python program and the options supplied by the command line call.
* **`default`**: A boolean (either `true` or `false` or not given) whether or not the current entry is the default. You yourself are responsible for preventing multiple defaults.
* **`source_folder`**: Usually, Simpler Rsync is expected to work from the current directory of invocation. Setting this value changes this behavior explicitly. Useful in combination with `gather`, see next section.

**Note**: `remote_folder` and `local_folder` are deprecated and will be removed soon™! There's a handy little command in the warning to convert config files.

Additionally to the parameters of an entry, *global* parameters true for all entries in the config file can be specified. The parameters need to be specified before the first entry occurs. Currently, only `rsync_options` is supported. Example:

```toml
rsync_options = ['-v']

[firsthost]
    hostname = "first"
    # etc
```

### Inverse Transfers (Gathering)
Simpler Rsync also supports transfers from a remote host to the local machine (a gathering operation). An entry in the config file as an example looks like this:

```toml
[inversehost]
    hostname = "second"
    source_folder = "/some/thing/"
    target_folder = "/some/thang/"
    gather = true
    rsync_options = ["--update"]
```

The `gather` option is the important one. It switches the order of source and destination in the underlying `rsync` call.

### Local Transfers
For copying on the same machine, Simpler Rsync supports *host-less* operations between a source directory and a target directory. This mode is enabled if the `hostname` key of the respective entry in the config file is missing. In this case, the script also checks for `target_folder` to be a valid directory on the current machine. Example config file:

```toml
[localstuff]
    target_folder = "/dev/null/"
```

## Dependencies
Some Python packages are required for Simpler Rsync. All can be installed with `pip`:

```bash
pip install sh toml click
```
