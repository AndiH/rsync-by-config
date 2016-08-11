from setuptools import setup

setup(
	name='rsync-by-config',
	version='2.3b',
	author='Andreas Herten',
	author_email='a.herten@gmail.com',
	url='https://github.com/AndiH/rsync-by-config',
	description='Call Rsync by configuration files in current directory. Monitoring and different targets possibly.',
	py_modules=['rbc'],
	install_requires=[
		'Click',
		'sh',
		'toml',
		'watchdog'
	],
    entry_points='''
        [console_scripts]
        rbc=rbc:setupToolsWrap
    ''',
	scripts=['rbc.py']  # Will be deprecated soon!
)
