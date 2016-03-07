from setuptools import setup

setup(
	name='simpler-rsync',
	version='1.4',
	author='Andreas Herten',
	url='https://github.com/AndiH/simpler-rsync',
	# py_modules=['simpler-rsync'],
	install_requires=[
		'Click',
		'sh',
		'toml'
	],
	# entry_points={
	# 	'console_scripts': ['mysync=sync:main']
	# }
	scripts=['sync.py']
)
