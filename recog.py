import json

from fbrecog import recognize

with open('fb.json') as fb_config:
    config = json.load(fb_config)

path = 'pic.jpg'
access_token = config['access_token']
cookie = config['cookie']
fb_dtsg = config['fb_dtsg']

print (recognize(path, access_token, cookie, fb_dtsg))
