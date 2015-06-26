"""grabs a gif and posts it in slack"""
import requests, os, sys
import resources as rs
def __main__():
    token = os.getenv('stoken')
    tag = str(sys.argv[1])
    channel = str(sys.argv[2])

    requrl = "http://api.giphy.com/v1/gifs/search?q=" + tag + "?api_key=dc6zaTOxFJmzC"

    try:
        gifjson = requests.get(requrl, timeout=5).json()
        gifurl = gifjson[u"data"][u"image_url"]
    except:
        gifurl = 'Sorry bruv, no gifs found with tag(s): ' + tag

    rs.post(channel, gifurl, 'shades McGee (gif extraordinaire)', token, icon_emoji=":gif:")

__main__()
