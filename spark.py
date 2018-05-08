from pyspark import SparkConf, SparkContext
from pyspark.streaming import StreamingContext
import json
from textblob import TextBlob
from elasticsearch import Elasticsearch

TCP_IP = 'localhost'
TCP_PORT = 9001

# Pyspark
# create spark configuration
conf = SparkConf()
conf.setAppName('TwitterApp')
conf.setMaster('local[2]')
# create spark context with the above configuration
sc = SparkContext(conf=conf)

# create the Streaming Context from spark context with interval size 2 seconds
ssc = StreamingContext(sc, 4)
ssc.checkpoint("checkpoint_TwitterApp")
# read data from port 900
dataStream = ssc.socketTextStream(TCP_IP, TCP_PORT)

######### your processing here ###################
dataStream = dataStream.map(lambda t:load_json(t))
dataStream = dataStream.map(lambda t:get_tweet_sentiment(t))
out=dataStream.foreachRDD(lambda t: t.foreachPartition(lambda x:ES_connector(x)))

def get_tweet_sentiment(tweet_json):
	tweet_text = tweet_json['tweet']
	result = TextBlob(tweet_text)
        # create TextBlob object of passed tweet text
	sentiment_polarity = result.sentiment.polarity
        # set sentiment

        if(sentiment_polarity > 0):
		tweet_json['sentiment'] = 'positive'
		return(tweet_json)

	elif(sentiment_polarity == 0):
		tweet_json['sentiment'] = 'neutral'
		return(tweet_json)
	else:
		tweet_json['sentiment'] = 'negative'
		return(tweet_json)

def load_json(x):
	x = json.loads(x)
	return(x)

def ES_connector(partition):
	tweets = list(partition)
	print(tweets,len(tweets))
	mapping = None
	es = Elasticsearch([{'host': 'localhost', 'port': 9200}])  
	
# if index already exists
	if(es.indices.exists(index = "location")):
		if(len(tweets) != 0):
			for tweet in tweets:
				doc = {
					"text": tweet['tweet'],
					"location": {
							"lat": tweet['coords'][0],
							"lon": tweet['coords'][1]
							},
					"sentiment":tweet['sentiment']
				}
				if(tweet['coords'][0] != 0 and tweet['coords'][1] !=0 ):
					es.index(index="location", doc_type='request-info', body=doc)
		else:
			print("No tweets")
		
# if index does not exists, create a new one
	else:
		mapping = {
			"mappings": {
				"request-info": {
					"properties": {
						"text": {"type": "text"},
						"location": {"type": "geo_point"},
						"sentiment": {"type": "text"}                        
					}
				}
			}
		}

		es.indices.create(index='location', body=mapping)
		if(len(tweets) != 0):
			for tweet in tweets:                
				doc = {
					"text": tweet['tweet'],
					"location": {
						"lat": tweet['coords'][0],
						"lon": tweet['coords'][1]
						},
					"sentiment":tweet['sentiment']
                    }
				if(tweet['coords'][0] != 0 and tweet['coords'][1] !=0 ):
					es.index(index="location", doc_type='request-info', body=doc)


#################################################
dataStream.pprint()
ssc.start()
ssc.awaitTermination()
