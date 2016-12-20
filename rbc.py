#!/usr/bin/env python3
# sync.py by Andreas Herten, Feb+ 2016

import os
from datetime import datetime
import time
import fnmatch
import click
import toml
from sh import rsync

try:
	from watchdog.observers import Observer
	from watchdog.events import FileSystemEventHandler
	thereIsWatchDog = True
except ImportError:
	thereIsWatchDog = False
	print("# Watchdog package not found; monitoring capabilities not available.")


class syncObject(object):
	"""One sync target and its configuration. More or less equal to one config file entry, parsed."""
	def __init__(self, host_toml, localDir, destDir, rsync_options, dryrun, gather, config_file, verbose):
		self.host_toml = host_toml
		self.localDir = localDir
		self.destDir = destDir
		self.rsync_options = rsync_options
		self.dryrun = dryrun
		self.gather = gather
		self.config_file = config_file
		self.verbose = verbose

class rbcObj(object):
	"""Holds all state information of the syncing process."""
	def __init__(self, verbose, configFilename):
		self.verbose = verbose
		self.configFilename = configFilename
		self.currentDir = os.getcwd()
		self.configFilenameAbs = os.path.join(currentDir, configFilename)


def sync(synObj):
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
	rsync_opts.append('--exclude=' + synObj.config_file)
	if synObj.dryrun:
		if synObj.verbose:
			print("# --dryrun is turned ON!")
		rsync_opts.append("--dry-run")  # no transfer, just report
	if 'rsync_options' in synObj.host_toml:
		for option in synObj.host_toml['rsync_options']:
			rsync_opts.append(option)
	for option in synObj.rsync_options:
		rsync_opts.append(str(option))

	if synObj.verbose:
		print("# All rsync options: {}".format(rsync_opts))

	synObj.sourceDir = synObj.localDir + "/"  # make sure it has a trailing slash, for rsync
	if 'hostname' in synObj.host_toml:
		synObj.destDir = str(synObj.host_toml['hostname']) + ":" + synObj.destDir

	if synObj.gather:
		synObj.sourceDir, synObj.destDir = synObj.destDir, synObj.sourceDir

	print(rsync(rsync_opts, synObj.sourceDir, synObj.destDir))


def loadConfig(verbose, filename):
	with open(filename) as f:
		config = toml.loads(f.read())
	if verbose:
		print("# Loaded config file {}".format(filename))
	return config


if thereIsWatchDog:
	class syncEventHandler(FileSystemEventHandler):
		def __init__(self, action=None):
			super(syncEventHandler, self).__init__()
			self.action = action
			self.counter = 0
		def getCounter(self):
			return self.counter
		def on_any_event(self, event):
			super(syncEventHandler, self).on_any_event(event)

			# print("Event!")
			eligableForSync = False
			if not os.path.isdir(event.src_path) and ".git" not in event.src_path and not fnmatch.fnmatch(event.src_path, ".*.tmp"):
				eligableForSync = True
			if self.action is not None and eligableForSync:
				self.counter += 1
				print("~~ Sync {} at {}".format(self.counter, datetime.now()))
				self.action()


def listHosts(verbose, config, configFile):
	if (verbose):
		print("# Listing available host files")
	print("Specified entries in {} are:".format(configFile))
	for en in config:
		currentEntry = config[en]
		if isinstance(currentEntry, dict):
			print("\t {}".format(en))
			if (verbose):
				for (key, entry) in currentEntry.items():
					print("\t\t {}: {}".format(key, entry))
				print("\n")


def sanityCheckConfigFile(configFile):
	if not os.path.isfile(configFile):
		print("Please make sure {} exists in the current directory!".format(configFile))
		exit()


def parseGlobalRsyncOptions(verbose, config):
	globalOptions = []
	"""This parses the global Rsync options specified at the very top of a TOML file."""
	if "rsync_options" in config:
		if verbose:
			print("# A global rsync_options key is given in the config file.")
		rawOptions = config["rsync_options"]
		if type(rawOptions) is list:
			for option in config["rsync_options"]:
				globalOptions.append(str(option))
		else:
			globalOptions.append(str(rawOptions))
		if verbose:
			print("# List of rsync options due to command line and global key in config file: {}".format(globalOptions))
	return globalOptions


def parseDefaultEntry(verbose, config):
	if verbose:
		print("# No entry was explicitly specified; trying to determine from config file")
	entry = list(config.keys())[-1]
	for en in config:
		if "default" in config[en]:
			if config[en]["default"] is True:
				entry = en
				print("# Found default entry {}".format(en))
				print("Using entry: {}".format(en))
	return (entry, False)  # Multi host default entry not yet supported


def sanityCheckEntries(verbose, entries, config, configFile):
	for entry in entries:
		if entry not in config:
			print("No entry {} is known in {}. Please edit the file!".format(entry, os.path.basename(configFile)))
			listHosts(verbose, config, configFile)
			exit()


def parseMultiEntries(verbose, entry, config, configFile):
	multihost = False
	entries = entry.split(",")
	if len(entries) > 1:
		multihost = True
	sanityCheckEntries(verbose, entries, config, configFile)
	if verbose:
		if multihost:
			print("Using entries " + ", ".join(entries) + ".")
		else:
			print("# Using entry {}".format(entries))
	return (entries, multihost)


def parseEntry(verbose, config, configFile, entry):
	if entry == "":
		(entry, multihost) = parseDefaultEntry(verbose, config)
	else:
		(entry, multihost) = parseMultiEntries(verbose, entry, config, configFile)
	return (entry, multihost)


def parseSourceDirectory(verbose, currentDir, configFilename, entry_toml):
	sourceDir = currentDir
	if ('local_folder' or 'source_folder') in entry_toml:
		if 'source_folder' in entry_toml:
			sourceDirUntested = entry_toml['source_folder']
		else:
			print("Warning: Key `local_folder` is deprecated. Please use `source_folder`!\nThe following command will in-place modify the file:\n\tsed -i -- 's/local_folder/source_folder/g' {}".format(configFilename))
			sourceDirUntested = entry_toml['local_folder']
		if not (os.path.isdir(sourceDirUntested) and os.path.exists(sourceDirUntested)):
			print("You specified the source folder {} to be synced. This folder does not exist!".format(sourceDirUntested))
			exit()
		sourceDir = sourceDirUntested
		if verbose:
			print("# Running with explicit source folder {}".format(sourceDir))
	if verbose:
		print("# Using source folder {}".format(sourceDir))
	return sourceDir


def parseTargetDirectory(verbose, entry, configFilename, entry_toml):
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
	return destDir


def sanityCheckTarget(verbose, destDir, entry_toml):
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


def checkIfGather(verbose, localDir, entry_toml):
	gather = False
	if 'gather' in entry_toml:
		if verbose:
			print("# --gather is turned ON! Collecting to {}".format(localDir))
		gather = True
	return gather


@click.command()
@click.option("--monitor", "-m", is_flag=True, default=False, help="Run in monitor mode.")
@click.option("--config_file", default=".sync.toml", help="Name of configuration file. The default is '.sync.toml'.")
@click.option("--rsync_options", "-o", default="", type=str, multiple=True, help="Additional options to call rsync with.")
@click.option("--dryrun", is_flag=True, help="Call rsync as a dry run.")
@click.option("--verbose", is_flag=True, help="Run with output information.")
@click.option("--listhosts", is_flag=True, help="List available hosts in config_file.")
@click.argument('entry', default="")
def main(entry, monitor, config_file, rsync_options, dryrun, verbose, listhosts):
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
		print("# Running {} in verbose mode. All verbosity commands are prefixed with #. Current datetime: {}".format(os.path.basename(__file__), datetime.now()))

	# Check if monitoring is enabled; checking is also done on import
	if monitor:
		if not thereIsWatchDog:
			print("Sorry, package Watchdog not found. Monitoring not possible.")
		if verbose and thereIsWatchDog:
			print('# Running in monitor mode.')

	configFilename = config_file
	currentDir = os.getcwd()
	configFile = os.path.join(currentDir, configFilename)

	rbcSyncer = rbcObj(verbose, configFilename)


	## Configuration file parsing
	sanityCheckConfigFile(configFile)
	config = loadConfig(verbose, configFile)

	# Check for command line rsync parameters
	rsync_options = list(rsync_options)

	# List hosts, if user flags it
	if listhosts:
		listHosts(verbose, config, configFile)
		exit()

	# Globals
	rsync_options = rsync_options + parseGlobalRsyncOptions(verbose, config)

	# Try to determine which entry to take from the config file
	(entry, multihost) = parseEntry(verbose, config, configFile, entry)

	if multihost:
		# HANDLE MULTIHOST
		print("Multihost only supported up to this stage of the program.")
		exit()
	else:
		# DEFAULT CASE FOR NOW
		print("No multihost")
	entry_toml = config[entry[0]]

	## Source directory parsing
	localDir = parseSourceDirectory(verbose, currentDir, configFilename, entry_toml)

	## Target directory parsing
	destDir = parseTargetDirectory(verbose, currentDir, configFilename, entry_toml)

	### Target = remote OR target = local?
	sanityCheckTarget(verbose, destDir, entry_toml)

	## Invert source and target?
	gather = checkIfGather(verbose, localDir, entry_toml)

	## Put into syncObject
	remote = syncObject(entry_toml, localDir, destDir, rsync_options, dryrun, gather, config_file, verbose)

	## Set up monitoring
	syncer = lambda: sync(remote)

	# syncer = lambda: map(sync, entry_toml, localDir, destDir, rsync_options, dryrun, gather, config_file, verbose)
	# syncer = lambda: [a(en) for en in strings][0]
	if monitor and thereIsWatchDog and not gather:
		event_handler = syncEventHandler(action = syncer)
		observer = Observer()
		observer.schedule(event_handler, localDir, recursive=True)
		observer.start()
		try:
			while True:
				time.sleep(1)
		except KeyboardInterrupt:
			print("~~ Stopping...")
			print("~~ Synced {} times in total".format(event_handler.getCounter()))
			observer.stop()
		observer.join()
	else:
		syncer()


if __name__ == '__main__':
	print("It looks like you called Rsync By Config via rbc.py!\n Consider using pip to install rbc as a package (with a command line tool): pip install https://github.com/AndiH/rsync-by-config/archive/master.zip.")
	main(auto_envvar_prefix='RBC')


def setupToolsWrap():
	main(auto_envvar_prefix='RBC')
