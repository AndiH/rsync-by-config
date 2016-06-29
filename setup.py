from setuptools import setup

setup(
	name='rsync-by-config',
	version='2.0',
	author='Andreas Herten',
	url='https://github.com/AndiH/rsync-by-config',
	# py_modules=['simpler-rsync'],
	install_requires=[
		'Click',
		'sh',
		'toml',
		'watchdog'
	],
	# entry_points={
	# 	'console_scripts': ['mysync=sync:main']
	# }
	scripts=['rbc.py']
)
