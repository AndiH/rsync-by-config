#!/usr/bin/env python
# sync.py by Andreas Herten, Feb+ 2016

import os
from datetime import datetime
import click
import toml
from sh import rsync

def sync(host_toml, localDir, destDir, rsync_options, dryrun, gather, config_file, verbose):
	rsync_opts = []
	rsync_opts.append("--archive")  # archive
	# rsync_opts.append("--update")  # skip files that are newer on the receiver
	rsync_opts.append("--human-readable")  # output numbers in a human-readable format
	rsync_opts.append("--verbose")  # increase verbosity
	rsync_opts.append("--recursive")  # recurse into directories
	rsync_opts.append("--compress")  # compress file data during the transfer
	rsync_opts.append("--cvs-exclude")  # auto-ignore files in the same way CVS does
	# rsync_opts.append("--delete")  # delete extraneous files from dest dirs
	# rsync_opts.append('--filter=\"dir-merge,- .gitignore\"')
	rsync_opts.append('--exclude=*.bin')
	rsync_opts.append('--exclude=' + config_file)
	if dryrun:
		if verbose:
			print("# --dryrun is turned ON!")
		rsync_opts.append("--dry-run")  # no transfer, just report
	if 'rsync_options' in host_toml:
		for option in host_toml['rsync_options']:
			rsync_opts.append(option)
	for option in rsync_options:
		rsync_opts.append(str(option))

	if verbose:
		print("# All rsync options: {}".format(rsync_opts))

	sourceDir = localDir + "/"  # make sure it has a trailing slash, for rsync
	if 'hostname' in host_toml:
		destDir = str(host_toml['hostname']) + ":" + destDir

	if gather:
		sourceDir, destDir = destDir, sourceDir

	print(rsync(rsync_opts, sourceDir, destDir))


def loadConfig(filename):
	with open(filename) as f:
		return toml.loads(f.read())


@click.command()
@click.option("--config_file", default=".sync.toml", help="Name of configuration file. The default is '.sync.toml'.")
@click.option("--rsync_options", "-o", default="", type=str, multiple=True, help="Additional options to call rsync with.")
@click.option("--dryrun", is_flag=True, help="Call rsync as a dry run.")
@click.option("--verbose", is_flag=True, help="Run with output information.")
@click.argument('entry', default="")
def main(entry, config_file, rsync_options, dryrun, verbose):
	"""Use the entry of ENTRY in config_file to synchronize the files of the current directory to. If ENTRY is not specified, the entry of config_file with 'default = true' is taken. If no default entry is specified, some entry is taken (which might be the first in the config file, but does not need to be).


	The structure of the config file should be of the following:

	[entry]\n
		hostname = \"remotecomputer\"\n
		target_folder = \"/user/myuser/directory/\"\n
		rsync_options = [\"--a\", \"--b\"]\n
		default = true

	Additional keywords for an entry in a config file are:\n
		* source_folder: Explicitly set the source directory to this value\n
		* gather: If true, switches the order of source and destination.

	For a full list of options see https://github.com/AndiH/rsync-by-config"""

	if verbose:
		print('# Running {} in verbose mode. All verbosity commands are prefixed with #. Current datetime: {}'.format(os.path.basename(__file__), datetime.now()))

	configFilename = config_file
	currentDir = os.getcwd()
	configFile = os.path.join(currentDir, configFilename)
	if not os.path.isfile(configFile):
		print("Please make sure {} exists in the current directory!".format(configFilename))
		exit()
	## Configuration file parsing
	config = loadConfig(configFile)
	rsync_options = list(rsync_options)
	if verbose:
		print("# Loaded config file {}".format(configFile))
	# Globals
	if "rsync_options" in config:
		if verbose:
			print("# A global rsync_options key is given in the config file.")
		for option in config["rsync_options"]:
			rsync_options.append(str(option))
		if verbose:
			print("# List of rsync options due to command line and global key in config file: {}".format(rsync_options))
	# Try to determine which entry to take from the config file
	if entry == "":
		if verbose:
			print("# No entry was explicitly specified; trying to determine from config file")
		entry = list(config.keys())[-1]
		for en in config:
			if "default" in config[en]:
				if config[en]["default"] is True:
					entry = en
					print("# Found default entry {}".format(en))
					print("Using entry: {}".format(en))
	else:
		if entry not in config:
			print("No entry {} is known in {}. Please edit the file!".format(entry, configFilename))
			print("Specified entries are:")
			for en in config:
				print("\t {}".format(en))
			exit()
	if verbose:
		print("# Using entry {}".format(entry))
	entry_toml = config[entry]
	## Source directory parsing
	localDir = currentDir
	if ('local_folder' or 'source_folder') in entry_toml:
		if 'source_folder' in entry_toml:
			localDirUntested = entry_toml['source_folder']
		else:
			print("Warning: Key `local_folder` is deprecated. Please use `source_folder`!\nThe following command will in-place modify the file:\n\tsed -i -- 's/local_folder/source_folder/g' {}".format(configFilename))
			localDirUntested = entry_toml['local_folder']
		if not (os.path.isdir(localDirUntested) and os.path.exists(localDirUntested)):
			print("You specified the source folder {} to be synced. This folder does not exist!".format(localDirUntested))
			exit()
		localDir = localDirUntested
		if verbose:
			print("# Running with explicit source folder {}".format(localDir))
	if verbose:
		print("# Using source folder {}".format(localDir))
	## Target directory parsing
	if (not "remote_folder" or not "target_folder") in entry_toml:
		print("The entry {} does not have a target folder location. Please edit {}!".format(entry, configFilename))
		exit()
	if "remote_folder" in entry_toml:
		print("Warning: Key `remote_folder` is deprecated. Please use `target_folder`!\nThe following command will in-place modify the file:\n\tsed -i -- 's/remote_folder/target_folder/g' {}".format(configFilename))
		destDir = entry_toml['remote_folder']
	if "target_folder" in entry_toml:
		destDir = entry_toml['target_folder']
	if verbose:
		print("# The target folder path is {}".format(destDir))
	### Target = remote OR target = local?
	if "hostname" not in entry_toml:
		if verbose:
			print("# No hostname specified. Targeting local transfers.")
		if not (os.path.isdir(destDir) and os.path.exists(destDir)):
			print("You specified the target folder {}. This folder does not exist!".format(destDir))
			exit()
		if verbose:
			print("# Running with local target folder {}".format(destDir))
	if "hostname" in entry_toml:
		if verbose:
			print("# The remote hostname is {}".format(entry_toml['hostname']))
	## Invert source and target?
	gather = False
	if 'gather' in entry_toml:
		if verbose:
			print("# --gather is turned ON! Collecting to {}".format(localDir))
		gather = True
	sync(entry_toml, localDir, destDir, rsync_options, dryrun, gather, config_file, verbose)

if __name__ == '__main__':
	main(auto_envvar_prefix='RBC')
