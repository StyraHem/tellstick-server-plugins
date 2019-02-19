#!/usr/bin/env python
# -*- coding: utf-8 -*-

try:
	from setuptools import setup
	from setuptools.command.install import install
	from setuptools.command.bdist_egg import bdist_egg
except ImportError:
	from distutils.core import setup
	from distutils.command.install import install
import os

class BuildwebInstall(install):
	def run(self):
		print("generate web application")
		if os.system('npm install') != 0:
			raise Exception("Could not install npm packages")
		if os.system('npm run build') != 0:
			raise Exception("Could not build web application")
		install.run(self)

class BuildwebEgg(bdist_egg):
	def run(self):
		print("generate web application")
		if os.system('npm install') != 0:
			raise Exception("Could not install npm packages")
		if os.system('npm run build') != 0:
			raise Exception("Could not build web application")
		bdist_egg.run(self)

setup(
	name='Shelly',
	version='0.1.0',
	icon='shelly.png',
	author='StyraHem / Tarra AB',
	author_email='info@styrahem.se',
	category='appliances',
	color='#26a69a',
	description='Shelly smart home devices',
	long_description='',
	packages=['shelly'],
	package_dir={'':'src'},
	cmdclass={  # Build web interface
		'install': BuildwebInstall,
		'bdist_egg': BuildwebEgg,
	},
	entry_points={ \
		'telldus.startup': ['c = shelly:Shelly [cREQ]']
	},
	extras_require=dict(cREQ='Base>=0.1\nTelldus>=0.1\nTelldusWeb>=0.1'),
	package_data={'shelly' : [
			'htdocs/img/*.png',
			'htdocs/style/*.css',
			'htdocs/*.js',
	]}
)
