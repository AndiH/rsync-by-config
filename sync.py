#!/usr/bin/env python
# sync.py by Andreas Herten, Feb 2016

import os
import click
import toml
from sh import rsync

def sync(host_toml, currentDir, rsync_options, dryrun):
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
	if dryrun:
		rsync_opts.append("--dry-run")  # no transfer, just report
	if host_toml.has_key('rsync_options'):
		for option in host_toml['rsync_options']:
			rsync_opts.append(option)
	for option in rsync_options:
		rsync_opts.append(str(option))

	sourceDir = "."
	destDir = str(host_toml['hostname']) + ":" + host_toml['remote_folder']

	print(rsync(rsync_opts, sourceDir, destDir))


def loadConfig(filename):
	with open(filename) as f:
		return toml.loads(f.read())

@click.command()
@click.option("--config_file", default=".sync.toml", help="Name of configuration file. The default is '.sync.toml'.")
@click.option("--rsync_options", "-o", default="", type=str, multiple=True, help="Additional options to call rsync with.")
@click.option("--dryrun", is_flag=True, help="Call rsync as a dry run.")
@click.argument('host', default="")
def main(host, config_file, rsync_options, dryrun):
	"""Use the entry of HOST in config_file to synchronize the files of the current directory to. If HOST is not specified, the entry of config_file with 'default = true' is taken. If no default host is specified, some host is taken (which might be the first in the config file, but does not need to be).


	The structure of the config file should be of the following:

	[host]\n
		hostname = \"remotecomputer\"\n
		remote_folder = \"/user/myuser/directory/\"\n
		rsync_options = [\"--a\", \"--b\"]\n
		default = true"""
	configFilename = config_file
	currentDir = os.getcwd()
	configFile = os.path.join(currentDir, configFilename)
	if not os.path.isfile(configFile):
		print("Please make sure {} exists in the current directory!".format(configFilename))
		exit()
	config = loadConfig(configFile)
	if host == "":
		host = config.keys()[-1]
		for h in config:
			print h
			if config[h].has_key("default"):
				if config[h]["default"] == True:
					host = h
	else:
		if not host in config:
			print("No host {} is known in {}. Please edit the file!".format(host, configFilename))
			exit()
	sync(config[host], currentDir, rsync_options, dryrun)

if __name__ == '__main__':
	main()
