from os import environ
from forms import PoemSubmissionForm
from flask import Flask, request, url_for, render_template
import spotipy
from nltk.tokenize import RegexpTokenizer, word_tokenize
from nltk.collocations import *
import nltk

DEBUG = environ['DEBUG']

app = Flask(__name__)
app.config.from_object(__name__)
spotify = spotipy.Spotify()
tokenizer = RegexpTokenizer(r'\w+')

@app.route('/', methods=['GET','POST'])
def home():
	form = PoemSubmissionForm(request.form)
	if request.method=='POST' and form.validate():
		poem = form.poem.data
		phrases = poemtoplaylist(poem)
		return render_template('index.html', form=form, phrases=phrases)
	else:
		return render_template('index.html', form=form, phrases={})

def poemtoplaylist(poem):
    tokenedpoem = tokenizer.tokenize(poem.lower())
    replaced = word_replace(tokenedpoem)
    playlist = flatten(replaced)
    indices = []
    for h in playlist:
        tokenedsong = tokenizer.tokenize(h['name'].lower())
        indices.append(find_index(tokenedsong, tokenedpoem))
    lenlist = [x['length'] for x in playlist]
    stop = map(lambda (x,y): x+y, zip(indices, lenlist))
    splitpoem= poem.split(' ')
    phrases = []

    if indices:
        if indices[0]!=0:
            toadd = {'words': str.join(' ',splitpoem[0:indices[0]]),
                             'song': False}
            phrases.append(toadd)
        for i in range(len(playlist)-1):
                toadd = {'words':str.join(' ',splitpoem[indices[i]:stop[i]]),
                         'song': True,
                         'data': playlist[i]
                         }
                phrases.append(toadd)
                toadd = {'words': str.join(' ',splitpoem[stop[i]:indices[i+1]]),
                             'song': False}
                phrases.append(toadd)
        toadd = {'words':str.join(' ',splitpoem[indices[-1]:stop[-1]]),
                         'song': True,
                         'data': playlist[-1]
                         }
        phrases.append(toadd)
        if len(splitpoem)>stop[-1]:
            toadd = {'words': str.join(' ',splitpoem[stop[-1]:]),
                             'song': False}
            phrases.append(toadd)

        return phrases
    else:
        return [{'words':poem}]

def find_index(sublist, searchlist):
    return [searchlist[i:i+len(sublist)]==sublist for i in xrange(len(searchlist)-len(sublist)+1)].index(True)

def word_replace(tokenlist):
    if type(tokenlist)!=list:
        return tokenlist
    else:
        bigram_measures = nltk.collocations.BigramAssocMeasures()

        finder = BigramCollocationFinder.from_words(tokenlist)

        # return the 10 n-grams with the highest PMI
        found = finder.nbest(bigram_measures.pmi, 1)
        if found:
            rarest = list(found[0])
            searchphrase = rarest[0]+' '+rarest[1]
            return [word_replace(x) for x in one_iteration(searchphrase, rarest, tokenlist)]
        #elif tokenedpoem:
        #    rarest = tokenedpoem
        #    searchphrase = tokenedpoem[0]
        else:
            return []

def flatten(x):
    result = []
    for item in x:
        if type(item)==list:
            result.extend(flatten(item))
        elif type(item)==dict:
            result.append(item)
    return result

def one_iteration(phrase, phraselist, tokenedlist):
    results = spotify.search('track:'+phrase, type='track', limit=30)
    searched = []
    for track in results['tracks']['items']:
        name = track['name']
        link = track['external_urls']['spotify']
        #image = track['album']['images'][0]['url']
        artist = track['artists'][0]['name']
        trackid = track['id']
        
        tokenedtrack = tokenizer.tokenize(name.lower())
        
        subset = any(tokenedlist[i:i+len(tokenedtrack)]==tokenedtrack for i in xrange(len(tokenedlist)-len(tokenedtrack)+1))
        length = len(tokenedtrack)
        tokenedname = tokenedtrack
        
        data = {
            'name': name,
            'link':link,
            'artist': artist,
            'trackid':trackid,
            'subset':subset,
            'length':length,
            'tokenedname':tokenedname
        }
        searched.append(data)
        
    longesttrue = sorted([x for x in searched if x['subset']], key=lambda x: x['length'], reverse=True)
    if not longesttrue:
        index = find_index(phraselist, tokenedlist)
        newpoem = [tokenedlist[0:index], tokenedlist[index+len(phraselist):]]
    else:
        longesttrue = longesttrue[0]
        index = find_index(longesttrue['tokenedname'],tokenedlist)
        newpoem = [tokenedlist[0:index], longesttrue, tokenedlist[index+longesttrue['length']:]]
    return newpoem

if __name__=='__main__':
	port = int(environ.get("PORT", 5000))
	app.run(host='0.0.0.0', port=port)