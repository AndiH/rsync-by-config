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
	def __init__(self, entry, globalCfg, host_toml):
		self.entry = entry
		self.globalCfg = globalCfg
		self.host_toml = host_toml
		# self.localDir = localDir
		# self.destDir = destDir
		self.rsync_options = self.globalCfg.rsync_options
		self.dryrun = self.globalCfg.dryrun
		# self.gather = gather
		self.config_file = self.globalCfg.configFilename
		self.verbose = globalCfg.verbose
	def parseSourceDirectory(self):
	# def parseSourceDirectory(verbose, currentDir, configFilename, entry_toml):
		"""Parse source directory and do some basic sanity checks."""
		sourceDir = self.globalCfg.currentDir
		if ('local_folder' or 'source_folder') in self.host_toml:
			if 'source_folder' in self.host_toml:
				sourceDirUntested = self.host_toml['source_folder']
			else:
				print("Warning: Key `local_folder` is deprecated. Please use `source_folder`!\nThe following command will in-place modify the file:\n\tsed -i -- 's/local_folder/source_folder/g' {}".format(self.globalCfg.configFilename))
				sourceDirUntested = self.host_toml['local_folder']
			if not (os.path.isdir(sourceDirUntested) and os.path.exists(sourceDirUntested)):
				print("You specified the source folder {} to be synced. This folder does not exist!".format(sourceDirUntested))
				exit()
			sourceDir = sourceDirUntested
			if self.verbose:
				print("# Running with explicit source folder {}".format(sourceDir))
		if self.verbose:
			print("# Using source folder {}".format(sourceDir))
		self.localDir = sourceDir
	def parseTargetDirectory(self):
	# def parseTargetDirectory(verbose, entry, configFilename, entry_toml):
		"""Parse target (old: remote) directory."""
		if (not "remote_folder" or not "target_folder") in self.host_toml:
			print("The entry {} does not have a target folder location. Please edit {}!".format(self.entry, self.globalCfg.configFilename))
			exit()
		if "remote_folder" in self.host_toml:
			print("Warning: Key `remote_folder` is deprecated. Please use `target_folder`!\nThe following command will in-place modify the file:\n\tsed -i -- 's/remote_folder/target_folder/g' {}".format(self.globalCfg.configFilename))
			destDir = self.host_toml['remote_folder']
		if "target_folder" in self.host_toml:
			destDir = self.host_toml['target_folder']
		if self.verbose:
			print("# The target folder path is {}".format(destDir))
		self.destDir = destDir
		self.sanityCheckTarget()
	def sanityCheckTarget(self):
		"""Do some limited sanity checking on target directory."""
	# def sanityCheckTarget(verbose, destDir, entry_toml):
		if "hostname" not in self.host_toml:
			if self.verbose:
				print("# No hostname specified. Targeting local transfers.")
			if not (os.path.isdir(self.destDir) and os.path.exists(self.destDir)):
				print("You specified the target folder {}. This folder does not exist!".format(self.destDir))
				exit(6)
			if self.verbose:
				print("# Running with local target folder {}".format(self.destDir))
		if "hostname" in self.host_toml:
			if self.verbose:
				print("# The remote hostname is {}".format(self.host_toml['hostname']))
	def checkIfGather(self):
		"""Check if gathering is enabled for entry."""
	# def checkIfGather(verbose, localDir, entry_toml):
		gather = False
		if 'gather' in self.host_toml:
			if self.verbose:
				print("# --gather is turned ON! Collecting to {}".format(self.localDir))
			gather = True
		self.gather = gather


class configParameters(object):
	"""Holds all state/global information of the syncing process."""
	def __init__(self, verbose, configFilename, dryrun):
		self.verbose = verbose
		self.configFilename = configFilename
		self.currentDir = os.getcwd()
		self.configFilenameAbs = os.path.join(self.currentDir, configFilename)
		self.rsync_options = None
		self.dryrun = dryrun
	def sanityCheckConfigFile(self):
		"""Sanity-test config file."""
		if not os.path.isfile(self.configFilenameAbs):
			print("Please make sure {} exists in the current directory!".format(self.configFilename))
			exit()
	def loadConfig(self):
		"""Read in TOML-structured config file."""
		with open(self.configFilenameAbs) as f:
			config = toml.loads(f.read())
		if self.verbose:
			print("# Loaded config file {}".format(self.configFilenameAbs))
		self.config = config
	def parseGlobalRsyncOptions(self):
		"""Parses the global Rsync options specified at the very top of a TOML file."""
		globalOptions = []
		if "rsync_options" in self.config:
			if self.verbose:
				print("# A global rsync_options key is given in the config file.")
			rawOptions = self.config["rsync_options"]
			if type(rawOptions) is list:
				for option in self.config["rsync_options"]:
					globalOptions.append(str(option))
			else:
				globalOptions.append(str(rawOptions))
			if self.verbose:
				print("# List of rsync options due to command line and global key in config file: {}".format(globalOptions))
		self.rsync_options = self.rsync_options + globalOptions


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


def listHosts(config):
	if (config.verbose):
		print("# Listing available host files")
	print("Specified entries in {} are:".format(config.configFilename))
	for en in config.config:
		currentEntry = config.config[en]
		if isinstance(currentEntry, dict):
			print("\t {}".format(en))
			if (config.verbose):
				for (key, entry) in currentEntry.items():
					print("\t\t {}: {}".format(key, entry))
				print("\n")


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
	return ([entry], False)  # Multi host default entry not yet supported


def sanityCheckEntries(cfg, entries):
	for entry in entries:
		if entry not in cfg.config:
			print("No entry {} is known in {}. Please edit the file!".format(entry, cfg.configFilename))
			listHosts(cfg)
			exit(5)


def parseMultiEntries(cfg, entry):
	multihost = False
	entries = entry.split(",")
	if len(entries) > 1:
		multihost = True
	sanityCheckEntries(cfg, entries)
	if cfg.verbose:
		if multihost:
			print("Using entries " + ", ".join(entries) + ".")
		else:
			print("# Using entry {}".format(entries))
	return (entries, multihost)


def parseEntry(cfg, entry):
	if entry == "":
		(entry, multihost) = parseDefaultEntry(cfg.verbose, cfg.config)
	else:
		(entry, multihost) = parseMultiEntries(cfg, entry)
	return (entry, multihost)


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

	cfgPars = configParameters(verbose, configFilename, dryrun)

	## Configuration file parsing
	cfgPars.sanityCheckConfigFile()
	cfgPars.loadConfig()

	# List hosts, if user flags it
	if listhosts:
		listHosts(cfgPars)
		exit()

	# Check for command line rsync parameters
	cfgPars.rsync_options = list(rsync_options)

	# Parse global rsync parameters (other global settings should be parsed here as well)
	cfgPars.parseGlobalRsyncOptions()

	# Try to determine which entry to take from the config file
	(entry, multihost) = parseEntry(cfgPars, entry)

	if multihost:
		# HANDLE MULTIHOST
		print("Multihost only supported up to this stage of the program.")
		exit()
	else:
		# DEFAULT CASE FOR NOW
		if verbose:
			print("No multihost")
		entry_toml = cfgPars.config[entry[0]]

	## Create syncObject
	remote = syncObject(entry, cfgPars, entry_toml)
	remote.parseSourceDirectory()
	remote.parseTargetDirectory()
	remote.checkIfGather()

	## Set up monitoring
	syncer = lambda: sync(remote)

	# syncer = lambda: map(sync, entry_toml, localDir, destDir, rsync_options, dryrun, gather, config_file, verbose)
	# syncer = lambda: [a(en) for en in strings][0]
	if monitor and thereIsWatchDog and not remote.gather:
		event_handler = syncEventHandler(action=syncer)
		observer = Observer()
		observer.schedule(event_handler, remote.localDir, recursive=True)
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
