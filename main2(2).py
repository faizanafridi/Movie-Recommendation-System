import pickle
import urllib
import numpy as np
import pandas as pd
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify

import urllib.request
import pickle
import requests
import json
import requests
import json

import bs4 as bs
from flask_sqlalchemy import SQLAlchemy

import bs4 as bs

my_api_key = 'fee15dbf316a148774d45f892bc49f4b';
tmdbId='652'
tmdbReviews=[]
for i in range(1,10):
    reviews = requests.get('https://api.themoviedb.org/3/movie/'+tmdbId+'/reviews?api_key='+my_api_key+'&language=en-US&page='+str(i))
    reviews = json.loads(reviews.content)
    reviews=reviews['results']
    for i in range(0,len(reviews)):
        print(i)
        tmdbReviews.append(reviews[i]['content'])
    if(len(reviews)==0):
        break
print("tmdb reviews",tmdbReviews)

imdbId='tt0332452'
movies = pickle.load(open('movies.pkl','rb'))
movies=pd.DataFrame(movies)
similarity = pickle.load(open('similarity.pkl','rb'))
bernoulli = pickle.load(open('bernoulli.pkl', 'rb'))
cv = pickle.load(open('cv.pkl', 'rb'))

sauce = urllib.request.urlopen('https://www.imdb.com/title/{}/reviews?ref_=tt_urv'.format(imdbId)).read()
soup = bs.BeautifulSoup(sauce, 'lxml')
imdbReviews = soup.find_all("div", {"class": "text show-more__control"})
soup_result=imdbReviews
reviewsList = []  # list of reviews
reviewsSentiment = []  # list of comments (good or bad)


#
for reviews in soup_result:
    if reviews.string:
        reviewsList.append(reviews.string)
        # passing the review to our model
        movie_review_list = np.array([reviews.string])
        reviewVector = cv.transform(movie_review_list)
        pred = bernoulli.predict(reviewVector)
        reviewsSentiment.append('Good' if pred else 'Bad')
for reviews in tmdbReviews:
        reviewsList.append(reviews)
        # passing the review to our model
        movie_review_list = np.array([reviews])
        reviewVector = cv.transform(movie_review_list)
        pred = bernoulli.predict(reviewVector)
        reviewsSentiment.append('Good' if pred else 'Bad')


# combining reviews and comments into a dictionary
movieReviews = {reviewsList[i]: reviewsSentiment[i] for i in range(len(reviewsList))}

print("len of reviews",len(movieReviews))
bad=0
good=0
reviewsPercentage=0
for i in movieReviews.values():
    if i=="Good":
        good+=1;
reviewsPercentage=good/len(movieReviews.values())*100

print(reviewsPercentage,"% good reviews")