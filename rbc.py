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
	def __init__(self, entryName, globalCfg):
		self.entry = entryName
		self.globalCfg = globalCfg
		self.host_toml = globalCfg.config[entryName]
		# self.localDir = localDir
		# self.destDir = destDir
		self.rsync_options = self.globalCfg.rsync_options
		self.dryrun = self.globalCfg.dryrun
		# self.gather = gather
		self.config_file = self.globalCfg.configFilename
		self.verbose = globalCfg.verbose
		self.multihost = globalCfg.multihost

		self.setup()

	def setup(self):
		"""Run different child routines to setup folders and options."""
		self.parseSourceDirectory()
		self.parseTargetDirectory()
		self.checkIfGather()

	def parseSourceDirectory(self):
		"""Parse source directory and do some basic sanity checks."""
		sourceDir = self.globalCfg.currentDir
		if 'local_folder' in self.host_toml or 'source_folder' in self.host_toml:
			if 'source_folder' in self.host_toml:
				sourceDirUntested = self.host_toml['source_folder']
			else:
				print("Warning: Key `local_folder` is deprecated. Please use `source_folder`!\nThe following command will in-place modify the file:\n\tsed -i -- 's/local_folder/source_folder/g' {}".format(self.globalCfg.configFilename))
				sourceDirUntested = self.host_toml['local_folder']
			if not (os.path.isdir(sourceDirUntested) and os.path.exists(sourceDirUntested)):
				print("You specified the source folder {} to be synced. This folder does not exist!".format(sourceDirUntested))
				exit(6)
			sourceDir = sourceDirUntested
			if self.verbose:
				print("# Running with explicit source folder {}".format(sourceDir))
		if self.verbose:
			print("# Using source folder {}".format(sourceDir))
		self.localDir = sourceDir

	def parseTargetDirectory(self):
		"""Parse target (old: remote) directory."""
		if not (("remote_folder" in self.host_toml) or ("target_folder" in self.host_toml)):
			print("The entry {} does not have a target folder location. Please edit {}!".format(self.entry, self.globalCfg.configFilename))
			exit(7)
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
		if "hostname" not in self.host_toml:
			if self.verbose:
				print("# No hostname specified. Targeting local transfers.")
			if not (os.path.isdir(self.destDir) and os.path.exists(self.destDir)):
				print("You specified the target folder {}. This folder does not exist!".format(self.destDir))
				exit(8)
			if self.verbose:
				print("# Running with local target folder {}".format(self.destDir))
		if "hostname" in self.host_toml:
			if self.verbose:
				print("# The remote hostname is {}".format(self.host_toml['hostname']))

	def checkIfGather(self):
		"""Check if gathering is enabled for entry."""
		gather = False
		if 'gather' in self.host_toml:
			if self.verbose:
				print("# --gather is turned ON! Collecting to {}".format(self.localDir))
			gather = True
		self.gather = gather


class globalParameters(object):
	"""Holds all state/global information of the syncing process."""
	def __init__(self, verbose, configFilename, dryrun):
		self.verbose = verbose
		self.configFilename = configFilename
		self.currentDir = os.getcwd()
		self.configFilenameAbs = os.path.join(self.currentDir, configFilename)
		self.rsync_options = None
		self.dryrun = dryrun
		self.multihost = None

	def sanityCheckConfigFile(self):
		"""Sanity-test config file."""
		if not os.path.isfile(self.configFilenameAbs):
			print("Config file not found! Please make sure {} exists in the current directory!".format(self.configFilename))
			exit(3)

	def loadConfig(self):
		"""Read in TOML-structured config file."""
		self.sanityCheckConfigFile()
		with open(self.configFilenameAbs) as f:
			config = toml.loads(f.read())
		if self.verbose:
			print("# Loaded config file {}".format(self.configFilenameAbs))
		self.config = config

	def parseGlobalRsyncOptions(self):
		"""Parse global Rsync options specified at the very top of a TOML file."""
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

	def parseRsyncOptions(self, cmdline_rsync_opts):
		"""Parse Rsync options"""
		self.rsync_options = list(cmdline_rsync_opts)
		self.parseGlobalRsyncOptions()


def sync(synObj):
	"""Setup rsync with options from different sources and run rsync"""
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

	sourceDir = synObj.localDir + "/"  # make sure it has a trailing slash, for rsync
	destDir = synObj.destDir
	if 'hostname' in synObj.host_toml:
		destDir = str(synObj.host_toml['hostname']) + ":" + synObj.destDir

	if synObj.gather:
		sourceDir, destDir = destDir, sourceDir

	if synObj.multihost:
		print("Syncing with {}".format(synObj.entry))
	print(rsync(rsync_opts, sourceDir, destDir))


if thereIsWatchDog:
	class syncEventHandler(FileSystemEventHandler):
		"""Event handler for watchdog"""
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
				for act in self.action:
					act()


def listHosts(config):
	"""List all available hosts in TOML config file"""
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
	"""Search for config file entry with default = True"""
	if verbose:
		print("# No entry was explicitly specified; trying to determine from config file")
	entry = list(config.keys())[-1]
	for en in config:
		if "default" in config[en]:
			if config[en]["default"] is True:
				entry = en
				print("# Found default entry {}".format(en))
				print("Using entry: {}".format(en))
	return [entry]  # Multi host default entry not yet supported


def sanityCheckEntries(cfg, entries):
	"""Check if command-line-given entry(/ies) are found in config file."""
	for entry in entries:
		if entry not in cfg.config:
			print("No entry {} is known in {}. Please edit the file!".format(entry, cfg.configFilename))
			listHosts(cfg)
			exit(4)


def parseMultiEntries(cfg, entry):
	"""Parse one or more entries to synchronize with."""
	entries = entry.split(",")
	sanityCheckEntries(cfg, entries)
	if cfg.verbose:
		if cfg.multihost:
			print("Using entries " + ", ".join(entries) + ".")
		else:
			print("# Using entry {}".format(entries))
	return entries

def isMultiremote(entries):
	"""Determine if more than one remote host is requested"""
	entries = entries.split(",")
	if len(entries) > 1:
		return True
	else:
		return False


def parseEntries(cfg, entry):
	"""Caller routine to determine target host(s)"""
	if entry == "":
		return parseDefaultEntry(cfg.verbose, cfg.config)
	else:
		return parseMultiEntries(cfg, entry)


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

	cfgPars = globalParameters(verbose, config_file, dryrun)

	# Configuration file parsing
	cfgPars.loadConfig()

	# List hosts, if user flags it
	if listhosts:
		listHosts(cfgPars)
		exit()

	# Parse global and command line rsync parameters
	cfgPars.parseRsyncOptions(rsync_options)

	# Try to determine which entry to take from the config file
	cfgPars.multihost = isMultiremote(entry)
	parsedEntries = parseEntries(cfgPars, entry)

	# Create syncObjects
	remotes = [syncObject(entr, cfgPars) for entr in parsedEntries]

	# Set up monitoring
	syncers = [lambda z=entry: sync(z) for entry in remotes]

	# syncer = lambda: map(sync, entry_toml, localDir, destDir, rsync_options, dryrun, gather, config_file, verbose)
	# syncer = lambda: [a(en) for en in strings][0]
	if monitor and thereIsWatchDog:
		for remote in remotes:
			if remote.gather:
				print("{} entry is configured to gather from remote to local. This does not work in monitoring configurtion.".format(remote.entry))
				exit(7)
			if 'local_folder' in remote.host_toml or 'source_folder' in remote.host_toml:
				if cfgPars.multihost:
					print("{current_entry} entry specifies a source directory for monitoring, {current_localDir}. Note that only the source directory of the first entry, {first_localDir}, is monitored!".format(current_entry=remote.entry, current_localDir=remote.localDir, first_localDir=remotes[0].localDir))
		event_handler = syncEventHandler(action=syncers)
		observer = Observer()
		observer.schedule(event_handler, remotes[0].localDir, recursive=True)
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
		for syncer in syncers:
			syncer()


if __name__ == '__main__':
	print("It looks like you called Rsync By Config via rbc.py!\n Consider using pip to install rbc as a package (with a command line tool): pip install https://github.com/AndiH/rsync-by-config/archive/master.zip.")
	main(auto_envvar_prefix='RBC')


def setupToolsWrap():
	main(auto_envvar_prefix='RBC')
