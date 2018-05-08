import json 
import tweepy
import socket
import re
import urllib
import requests

ACCESS_TOKEN = '146408693-Jj5FhdwyF9OQpd8AtuUBydvDmQrKb3TPi4H2obIT'
ACCESS_SECRET = 'H3QoGhd1I3BmTDoo9mtGFKDRClA9ZPV1alRn1k63QkSnx'
CONSUMER_KEY = 'd8KtW9XEJWqRRrGAyvEeqeKid'
CONSUMER_SECRET = 'D3hXSZgUXQWYM4fLIWmuRlQyO3S6bX1Ok5KLprjFcdwXJZbLqu'

auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
auth.set_access_token(ACCESS_TOKEN, ACCESS_SECRET)

hashtag = '#guncontrolnow'

TCP_IP = 'localhost'
TCP_PORT = 9001

# create sockets
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# s.connect((TCP_IP, TCP_PORT))
s.bind((TCP_IP, TCP_PORT))
s.listen(1)
conn, addr = s.accept()

class MyStreamListener(tweepy.StreamListener):
    def on_status(self, status):
	if status.user.location is not None:
		URL = "https://maps.googleapis.com/maps/api/geocode/json?address="+status.user.location+"&key=AIzaSyANVEgqqZ_03wIFMAdvMC-rxmRkkI46Hr8"
		#response = urllib.urlopen(url)                      #urllib causes encoding ASCII error
		#jsondata = json.loads(response.read())
		res = requests.get(url = URL)
		jsondata = res.json()
		if len(jsondata['results']) == 0:		#for handling list index out of range
			return
		if len(jsondata['results'][0]['address_components']) > 0:
			for i in jsondata['results'][0]['address_components']:
				if i['short_name'] == 'US':
					try:				#try block for handling list index out of range
						print(jsondata['results'][0]['geometry']['location'])
					except:
						return	
					lat = str(jsondata['results'][0]['geometry']['location']['lat'])
					lng = str(jsondata['results'][0]['geometry']['location']['lng'])
					alldata = {'tweet':self.clean_tweet(status.text),'location':status.user.location,'coords':[lat,lng]}
					sendjson = json.dumps(alldata)
					print(sendjson)        
					sendjson = sendjson + "\n"  
					print("===========================")
			       		conn.send(sendjson.encode('utf-8'))
    
    def on_error(self, status_code):
        if status_code == 420:
            return False
        else:
            print(status_code)
    
    def clean_tweet(self, tweet):
        return ' '.join(re.sub("(@[A-Za-z0-9]+)|([^0-9A-Za-z \t])|(\w+:\/\/\S+)", " ", tweet).split())

myStream = tweepy.Stream(auth=auth, listener=MyStreamListener())
myStream.filter(track=[hashtag])


