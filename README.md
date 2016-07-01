# Rsync By Config

I'm unable to remember the `rsync` options I usually need for transferring files to a remote location. Also, I'm too lazy to memorize the remote path. And of course I have a lot of different remotes with different directories. So I made a wrapper around `rsync` which reads from a config file in the current directory.

Rsync By Config was previously called *Simpler Rsync*.

## Getting Started

You can install Rsync By Config either with `pip install` or manually. Using `pip` is the recommended way (but it is not really tested beyond my OS X setups).

### With `pip`
This all-important one-liner should take care of pretty much everything:

```bash
pip install https://github.com/AndiH/rsync-by-config/archive/master.zip
```

You should have a command `rbc` now available in your shell. In the process, all dependencies should be installed as well.

Test it with

```bash
rbc --help
```

More manually but having the same effect, you could clone into some temporary directory and call `pip` into that directory:

```bash
cd $TMPDIR
git clone https://github.com/AndiH/rsync-by-config
cd rsync-by-config
pip install .
rbc --help
```

### Without `pip`

```bash
cd ~/bin/
git clone https://github.com/AndiH/rsync-by-config
ln -s rsync-by-config/rbc.py
rbc.py --help
```

You should insert `~/bin/` into your `$PATH`, e.g. via `export PATH=$HOME/bin/:$PATH` so you can use `rbc.py` globally from any folder. If `rbc.py` does not run, make sure to have installed all [dependencies](#dependencies). *Note: For the time being, a message about this being not the ideal way to invoke rbc is printed. This will go away at some point.*

## Options
`rbc` reads from a configuration file in the current directory, i.e. `.sync.toml`. Depending on the parameters specified there, the content of a directory (e.g. the current one) is copied to a target location using `rsync`.

The Python script has a few command line options, all documented via `rbc --help`:

* **`ENTRY`**: The name of the entry in the config file to be used for synchronization. If not specified, the *default* entry is taken. If there's no default, the first entry is taken. Maybe, at least, since the read-in of the config file is not strongly controlled…
* **`--monitor`**: Run Rsync By Config in monitoring (or *deamon*) mode. This will monitor the source folder for changes and issue a synchronization if one occurs. The package [Watchdog](https://github.com/gorakhargosh/watchdog) is used for this. (A more manual alternative to Watchdog is the command line utility [`fswatch`](https://github.com/emcrisostomo/fswatch), which can invoke arbitrary programs when a folder is changed.)
* **`--config_file=somefile`**: Specify a different config file. The default is `.sync.toml`.
* **`--dryrun`**: Calls `rsync` with `--dryrun`, preventing all actual copies. Good for testing.
* **`--verbose`**: Output every step and test of the script.
* **`--rsync_options="--something"`**: Propagate `--something` to `rsync` as an additional option. Can be invoked multiple times. Shorthand: `-o`. The `rsync` option is given in addition to the basic, default options hardcoded into the script file and in addition to the options defined in the config file.

To specify values for the options globally, environment values can be set. This is handy if you don't like my choice of calling the default config file `.sync.toml` (see below) and want to change it. The command line options (at least the last three from the list above) are accessible as environment variables with a `RBC_` prefix, thanks to [Click](http://click.pocoo.org/). So, for example, to rename the default config file, do:

```bash
export RBC_CONFIG_FILE=.my.toml
rbc somehost
```

## Config File
The config file used for Rsync By Config is written in [TOML](https://github.com/toml-lang/toml). One entry in the config file is for one distinct parameter configuration, i.e. usually for one remote location. The config file is structured as follows.

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
* **`rsync_options`**: An array of strings of `rsync` options. They are used in addition to the default, basic options hardcoded into the Python program and the options supplied by the command line call.
* **`default`**: A boolean (either `true` or `false` or not given) whether or not the current entry is the default. You yourself are responsible for preventing multiple defaults.
* **`source_folder`**: Usually, Rsync By Config is expected to work from the current directory of invocation. Setting this value changes this behavior explicitly. Useful in combination with `gather`, see next section.

**Note**: `remote_folder` and `local_folder` are deprecated and will be removed soon™! There's a handy little command in the warning to convert config files.

Additionally to the parameters of an entry, *global* parameters true for all entries in the config file can be specified. The parameters need to be specified before the first entry occurs. Currently, only `rsync_options` is supported. Example:

```toml
rsync_options = ['-v']

[firsthost]
    hostname = "first"
    # etc
```

### Inverse Transfers (Gathering)
Rsync By Config also supports transfers from a remote host to the local machine (a gathering operation). An entry in the config file as an example looks like this:

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
For copying on the same machine, Rsync By Config supports *host-less* operations between a source directory and a target directory. This mode is enabled if the `hostname` key of the respective entry in the config file is missing. In this case, the script also checks for `target_folder` to be a valid directory on the current machine. Example config file:

```toml
[localstuff]
    target_folder = "/dev/null/"
```


## Dependencies
Some Python packages are required for Rsync By Config. All can be installed with `pip`:

```bash
pip install sh toml click watchdog
```

While non-essential for its core task, Watchdog is needed for the monitoring capabilities. The dependency is optional, though.

When chosen the recommended way of installing Rsync By Config itself via `pip`, all dependencies are installed in the process.
