#!/usr/bin/python

# by Alex Hirzel <alex@hirzel.us> under the MIT license

import pandas as pd
import numpy as np

import ephem
import urllib.request
import schedule
from datetime import datetime, timedelta
import mimetypes
import configparser
from time import sleep
import collections

import os
import errno



# from http://stackoverflow.com/questions/273192/check-if-a-directory-exists-and-create-it-if-necessary
def make_sure_path_exists(path):
    try:
        os.makedirs(path)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise



def downloadImage(camobj, event, ts='%H%M'):
	"""downloads an image of the specified cam"""

	img = urllib.request.urlopen(camobj.url)

	# amazing bug...
	#ext = mimetypes.guess_extension(img.headers['Content-Type'])
	#print(img.headers['Content-Type'])

	ext = '.jpg'
	outputFilename = os.path.join('/home/alhirzel/imgs', camid, event, camid + '_' + ts + ext)
	outputFilename = (datetime.now() - camobj.lag).strftime(outputFilename)
	make_sure_path_exists(os.path.dirname(outputFilename));

	print('Downloading ' + outputFilename)

	output = open(outputFilename, 'wb')
	output.write(img.read())
	output.close()



class CamObserver:
	"""
	Reads configuration values and calculates the needed sunrise/sunset times,
	adjusts them as appropriate to capture the sunrise/sunset and provides
	utility functions which return lists of these times.
	"""

	def __init__(self, name, cfg):
		"""
		Tuck data away into variables, start building the pyephem observer
		object as well.
		"""

		self._name = name
		self._cfg = cfg

		# start to initialize a shared ephem observer object
		self._obs = ephem.Observer()
		self._obs.lat = cfg.getfloat('latitude') * ephem.degree
		self._obs.long = cfg.getfloat('longitude') * ephem.degree
		self._obs.elev = cfg.getfloat('elevation', 0)

		# pull out other config variables...
		self._lag_seconds = cfg.getfloat('lagseconds', fallback=0)

		# default to civil twilight for rising and something empirical for "risen"
		self._below_horizon = cfg.getfloat('belowhorizon', -6) * ephem.degree
		self._above_horizon = cfg.getfloat('abovehorizon', 9) * ephem.degree

		# useful public things
		self.lag = timedelta(seconds = self._lag_seconds)
		self.url = cfg.get('url')


	def sunrise_capture_times(self, f = '1min'):
		"""
		Calculate times to capture sunrises (including any offset needed due to
		laggy webcams).
		"""

		self._obs.horizon = self._below_horizon
		t0 = ephem.localtime(self._obs.next_rising(ephem.Sun(), use_center=True))

		self._obs.horizon = self._above_horizon
		t1 = ephem.localtime(self._obs.next_rising(ephem.Sun(), use_center=True))

		return(pd.date_range(t0 + self.lag, t1 + self.lag, freq=f))


	def sunset_capture_times(self, f = '1min'):
		"""
		Calculate times to capture sunsets (including any offset needed due to
		laggy webcams).
		"""

		self._obs.horizon = self._above_horizon
		t0 = ephem.localtime(self._obs.next_setting(ephem.Sun(), use_center=True))

		self._obs.horizon = self._below_horizon
		t1 = ephem.localtime(self._obs.next_setting(ephem.Sun(), use_center=True))

		return(pd.date_range(t0 + self.lag, t1 + self.lag, freq=f))



# read the config file
conf = configparser.ConfigParser()
conf.read('webcams.ini')

# just do the first cam for now
camid = conf.sections()[0]

# build list of times we need to do things
o = CamObserver(camid, conf[camid])
r = pd.Series(lambda: downloadImage(o, 'sunrise_%Y%m%d'), index=o.sunrise_capture_times())
s = pd.Series(lambda: downloadImage(o, 'sunset_%Y%m%d'), index=o.sunset_capture_times())
queue = r.append(s).sort_index()

# simplistic scheduler, requires sorted queue
for ts, fun in queue.iteritems():
	#seconds_to_go = lambda: (ts - datetime.now() - timedelta(hours=6)).total_seconds()
	seconds_to_go = lambda: (ts - datetime.now()).total_seconds()
	if seconds_to_go() > 0: # didn't miss it
		while seconds_to_go() > 0.5:
			print("waiting %u, then I will take the next image..." % seconds_to_go())
			sleep(1)
		fun()

