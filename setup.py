from setuptools import setup

setup(
	name='sync',
	version='1.0',
	py_modules=['sync'],
	install_requires=[
		'Click',
		'sh',
		'toml'
	],
	entry_points='''
		[console_scripts]
		sync.py=sync:main
	'''
	)
