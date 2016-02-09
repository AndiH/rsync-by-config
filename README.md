# Simpler rsync

I'm unable to remember the `rsync` options I usually need for transferring files to a remote location. Also, I'm too lazy to memorize the remote path. So I made a wrapper around `rsync` which reads from a config file in the current directory.

## Getting Started

```bash
cd ~/bin/
git clone https://github.com/AndiH/simpler-rsync.git
ln -s simpler-rsync/sync.py
sync.py --help
```

You should insert `~/bin/` into your `$PATH`, e.g. via `export PATH=$HOME/bin/:$PATH` so you can use `sync.py` globally from any folder.

## Options
`sync.py` reads from a configuration file in the current directory. Depending on the parameters specified there, the content of the current directory is copied to a remote location using `rsync`.

The Python script has a few command line options, all documented via `./sync.py --help`:

* **`HOST`**: The name of the entry in the config file to be used for synchronization. If not specified, the *default* entry is taken. If there's no default, the first entry is taken. Maybe, at least, since the read-in of the config file is not strongly controlled…
* **`--config_file=somefile`**: Specify a different config file. The default is `.sync.toml`.
* **`--dryrun`**: Calls `rsync` with `--dryrun`, preventing all actual copies. Good for testing.
* **`--rsync_options="--something"`**: Propagate `--something` to `rsync` as an additional option. Can be invoked multiple times. Shorthand: `-o`. The `rsync` option is given in addition to the basic, default options hardcoded into the script file and in addition to the options defined in the config file.

## Config File
The config file used for Simpler Rsync is written in [TOML](https://github.com/toml-lang/toml). One entry in the config file is for one remote location. The config file is structured as follows.

```toml
[firsthost]
    hostname = "first"
    remote_folder = "/something/"
    rsync_options = ["--delete", "--update"]

[secondhost]
    hostname = "127.0.0.1"
    remote_folder = "/something/"
    rsync_options = []
    default = true
```

The available keys are:

* **`hostname`**: A hostname to be understood by `rsync`. Hint: Use aliases in your `~/.ssh/config/`!
* **`remote_folder`**: The remote directory to be syncing to.
* **`rsync_options`**: A array of strings of `rsync` options. They are used in addition to the default, basic options hardcoded into the Python program and the options supplied by the command line call.
* **`default`**: A boolean (either `true` or `false` or not given) whether or not the current entry is the default. You yourself are responsible for preventing multiple defaults.

## Dependencies
Some Python packages are required for Simpler Rsync. All can be installed with `pip`:

```bash
pip install sh toml click
```
