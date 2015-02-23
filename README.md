# camgrabber
Downloads webcams according to sunrise/sunset times

Very, very beta!

My plan is to make a foreground daemon that can be tucked away behind
tmux/screen and forgotten about. Right now I really need to add the following
features:

 - [ ] automatically cycle the queue (right now you will need to CTRL+C every day)
 - [ ] really support multiple webcams
 - [ ] add events so that you can compile .jpg -> .mpg and upload to YouTube daily

Minor stuff:

 - [ ] support an interval=? option for each webcam (Eagle Harbor for example
       only updates every 2 minutes)
 - [ ] don't block on every download; if a download stalls, this will halt the
       whole daemon


Resources for the future:

http://visvis.googlecode.com/hg/vvmovie/images2gif.py

