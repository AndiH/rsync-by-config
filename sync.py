#!/usr/local/opt/python/bin/python2.7
# sync.py by Andreas Herten, Feb 2016

import os
from datetime import datetime
import click
import toml
from sh import rsync

def sync(host_toml, localDir, rsync_options, dryrun, gather, config_file, verbose):
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
	destDir = str(host_toml['hostname']) + ":" + host_toml['remote_folder']

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
@click.argument('host', default="")
def main(host, config_file, rsync_options, dryrun, verbose):
	"""Use the entry of HOST in config_file to synchronize the files of the current directory to. If HOST is not specified, the entry of config_file with 'default = true' is taken. If no default host is specified, some host is taken (which might be the first in the config file, but does not need to be).


	The structure of the config file should be of the following:

	[host]\n
		hostname = \"remotecomputer\"\n
		remote_folder = \"/user/myuser/directory/\"\n
		rsync_options = [\"--a\", \"--b\"]\n
		default = true

	Additional config keywords are:\n
		* local_folder: Explicitly set the source directory to this value\n
		* gather: If true, switches the order of source and destination."""
	if verbose:
		print('# Running {} in verbose mode. All verbosity commands are prefixed with #. Current datetime: {}'.format(os.path.basename(__file__), datetime.now()))
	configFilename = config_file
	currentDir = os.getcwd()
	configFile = os.path.join(currentDir, configFilename)
	if not os.path.isfile(configFile):
		print("Please make sure {} exists in the current directory!".format(configFilename))
		exit()
	config = loadConfig(configFile)
	if verbose:
		print("# Loaded config file {}".format(configFile))
	if host == "":
		if verbose:
			print("# No host was explicitly specified; trying to determine from config file")
		host = config.keys()[-1]
		for h in config:
			if "default" in config[h]:
				if config[h]["default"] is True:
					host = h
					print("# Found default remote server {}".format(h))
					print("Using remote server: {}".format(h))
	else:
		if host not in config:
			print("No host {} is known in {}. Please edit the file!".format(host, configFilename))
			print("Specified hosts are:")
			for h in config:
				print("\t {}".format(h))
			exit()
	if verbose:
		print("# Using host entry {}".format(host))
	if "hostname" not in config[host]:
		print("The host entry {} does not have a hostname. Please edit {}!".format(host, configFilename))
		exit()
	if verbose:
		print("# The remote host name is {}".format(config[host]['hostname']))
	if not "remote_folder" in config[host]:
		print("The host entry {} does not have a remote folder location. Please edit {}!".format(host, configFilename))
		exit()
	if verbose:
		print("# The remote folder path is {}".format(config[host]['remote_folder']))
	localDir = currentDir
	if 'local_folder' in config[host]:
		if not (os.path.isdir(config[host]['local_folder']) and os.path.exists(config[host]['local_folder'])):
			print("You specified the local folder {} to be synced. This folder does not exist!".format(config[host]['local_folder']))
			exit()
		localDir = config[host]['local_folder']
		if verbose:
			print("# Running with explicit local folder {}".format(localDir))
	if verbose:
		print("# Using local folder {}".format(localDir))
	gather = False
	if 'gather' in config[host]:
		if verbose:
			print("# --gather is turned ON! Collecting to {}".format(localDir))
		gather = True
	sync(config[host], localDir, rsync_options, dryrun, gather, config_file, verbose)

if __name__ == '__main__':
	main(auto_envvar_prefix='SRSYNC')
