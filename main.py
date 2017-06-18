import os, time, math, requests, nltk, tkinter
from twitter import *
from nltk import ne_chunk, pos_tag, word_tokenize
from nltk.tree import Tree
from gensim import corpora, models, similarities
from lxml import html
from textblob import TextBlob as tb
from tkinter import *
from tkinter import messagebox
from config import token, token_key, con_secret, con_secret_key

t = Twitter(auth=OAuth(token, token_key, con_secret, con_secret_key))
def twitter_search_tweet(query,count):
	x=t.search.tweets(q=query,count=count,lang='en')
	return x

def wikipedia_search(query):
    url = 'https://en.wikipedia.org/w/api.php?action=query&format=json&titles='+ query +'&prop=extracts&exintro&explaintext'
    response = requests.get(url)
    return response.json()

def sentiment_analysis(sentence):
    sentence = tb(sentence)
    if (sentence.sentiment.polarity < -0.3):
        return 'neg'
    elif (sentence.sentiment.polarity > -0.3 and sentence.sentiment.polarity < 0.3):
        return 'neutral'
    else:
        return 'pos'

def tf(word, blob):
    return blob.words.count(word) / len(blob.words)

def n_containing(word, bloblist):
    return sum(1 for blob in bloblist if word in blob.words)

def idf(word, bloblist):
    return math.log(len(bloblist) / (1 + n_containing(word, bloblist)))

def tfidf(word, blob, bloblist):
    return tf(word, blob) * idf(word, bloblist)

def ne_tagging(text):
    chunked = ne_chunk(pos_tag(word_tokenize(text)))
    prev = None
    continuous_chunk = []
    current_chunk = []
    for i in chunked:
        if type(i) == Tree:
            current_chunk.append(" ".join([token for token, pos in i.leaves()]))
        elif current_chunk:
            named_entity = " ".join(current_chunk)
            if named_entity not in continuous_chunk:
                continuous_chunk.append(named_entity)
                current_chunk = []
            else:
                continue
    return continuous_chunk

def logic():
    stoplist = set('I a about an are as at be by com for from how in is it of on or that the this to was what when where who will with the www ? . ,'.split())
    new_doc = e1.get("0.0", END)
    query = new_doc.lower().split()
    documents = []
    sentiment_doc = []
    for item in query:
        if (item not in stoplist):
            twitter_response = twitter_search_tweet(item, 25)['statuses']
            for resp in twitter_response:
                documents.append(resp['text'])
                sentiment_doc.append(sentiment_analysis(resp['text']))
            wiki_response = wikipedia_search(item)['query']['pages']
            key = list(wiki_response.keys())
            if('extract' in wiki_response[key[0]]):
                documents.append(wiki_response[key[0]]['extract'])
                sentiment_doc.append(sentiment_analysis(wiki_response[key[0]]['extract']))

    twitter_response = twitter_search_tweet(new_doc, 25)['statuses']
    for resp in twitter_response:
        documents.append(resp['text'])
        sentiment_doc.append(sentiment_analysis(resp['text']))
    wiki_response = wikipedia_search(new_doc)['query']['pages']
    key = list(wiki_response.keys())
    if('extract' in wiki_response[key[0]]):
        documents.append(wiki_response[key[0]]['extract'])
        sentiment_doc.append(sentiment_analysis(wiki_response[key[0]]['extract']))

    # for blob in enumerate(documents):
    #     scores = {word: tfidf(word, blob, documents) for word in blob.words}
    #     sorted_words = sorted(scores.items(), key=lambda x: x[1])

    texts = [[word for word in document.lower().split() if word not in stoplist]
            for document in documents]

    for i, text in enumerate(texts):
        for j, word in enumerate(text):
            word = tb(word).words.singularize()
            if(word):
                texts[i][j] = word[0]

    from collections import defaultdict
    frequency = defaultdict(int)
    for text in texts:
        for token in text:
            frequency[token] += 1
    texts = [[token for token in text if frequency[token] > 0]
             for text in texts]

    dictionary = corpora.Dictionary(texts)
    corpus = [dictionary.doc2bow(text) for text in texts]

    lsi = models.LsiModel(corpus, id2word=dictionary, num_topics=2)
    vec_bow = dictionary.doc2bow(query)
    vec_lsi = lsi[vec_bow]

    index = similarities.MatrixSimilarity(lsi[corpus])
    sims = index[vec_lsi]
    sim_score = list(enumerate(sims))

    i = 0
    pscore = 0
    sentiment_query = sentiment_analysis(new_doc)
    for score in sim_score:
        if(sentiment_doc[i] == sentiment_query):
            if(score[1] == 1):
                pscore += 3
            elif(score[1] > 0.75):
                pscore += 5
            elif(score[1] > 0.25):
                pscore += 4
        else:
            if(score[1] == 1):
                pscore += 1
            elif(score[1] > 0.75):
                pscore += 1
            elif(score[1] > 0.25):
                pscore += 2
        i+=1

    if(pscore/len(documents) >= 3):
        messagebox.showinfo('Result','Possibly True!')
    elif(pscore/len(documents) < 3):
        messagebox.showinfo('Result','Possibly False!')

def on_entry_click(event):
    if e1.get("1.0") == 'Enter your query here':
       e1.delete("1.0", END)
       e1.config(fg = 'black')

def on_focusout(event):
    if e1.get('1.0') == '':
        e1.insert(INSERT, 'Enter your query here')
        e1.config(fg = 'grey')

root = tkinter.Tk()
root.title("That's Fake")
root.configure(background='white')
root.minsize(width=800, height=500)
root.resizable(width=False, height=False)

bg_img = PhotoImage(file='img/background.png')
btn_img = PhotoImage(file='img/button.png')
udl_img = PhotoImage(file='img/underline.png')

bg = Label(root, image=bg_img, width=800, height=500, bd=0, relief=FLAT)
bg.pack()

lg = Label(root, text="Thats Fake!", font=('Arial', 36), fg='#f06464', bg='#bae3f3')
lg.place(x=260, y=80)

e1 = Text(root, width=40, height=1, relief=FLAT)
e1.insert(INSERT, 'Enter your query here')
e1.bind('<FocusIn>', on_entry_click)
e1.bind('<FocusOut>', on_focusout)
e1.config(fg = 'grey')
e1.place(x=200, y=215)

b1 = Button(root, image=btn_img, command=logic, bd=0, relief=FLAT)
b1.place(x=525, y=215)

root.mainloop()
