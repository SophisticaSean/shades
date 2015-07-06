import requests, json, os, sys
from requests_oauthlib import OAuth1
import resources as rs

apptoken = "g9uAl2oo4Y1lkioWPSxSVJcmP"
appsecret = "ctWopK2Mptgm2qCizYzN0sBZuhToZHwv6KOrBrekSQEpXwGU3M"
mytoken = os.getenv('twittertoken')
mysecret = os.getenv('twittersecret')
token = os.getenv('stoken')

url = 'https://api.twitter.com/1.1/statuses/update.json'
tweet = str(sys.argv[1])
auth = OAuth1(apptoken, appsecret, mytoken, mysecret)
data = {"status": tweet}

send_tweet = requests.post(url, auth=auth, data=data)

if send_tweet.status_code == requests.codes.ok:
    message = "Successfully tweeted {}".format(tweet)
    rs.msg_sean(message, token)
else:
    message = "Was not able to tweet {} \r\n Reason: {}".format(tweet, send_tweet.text)
    rs.msg_sean(message, token)

