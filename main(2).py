import numpy as np
import pandas as pd
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify

import urllib.request
import pickle

import requests
import json

import bs4 as bs
from flask_sqlalchemy import SQLAlchemy

from werkzeug.security import check_password_hash, generate_password_hash
from flask_login import login_user, logout_user, login_required,LoginManager,UserMixin,current_user

app = Flask(__name__)
app.config['SECRET_KEY'] = 'thisismysecretkeydonotstealit'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite3'
db = SQLAlchemy(app)
#
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.init_app(app)


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(1000))

class UserRating(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    userId = db.Column(db.Integer)
    movieId = db.Column(db.Integer)
    rating = db.Column(db.Integer)

class RecommendedMovie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    userId = db.Column(db.Integer)
    tmdbId = db.Column(db.Integer)
    tmdbTitle = db.Column(db.Integer)
    tmdbPoster = db.Column(db.String(300))
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))



movies = pickle.load(open('movies.pkl','rb'))
movies=pd.DataFrame(movies)
similarity = pickle.load(open('similarity.pkl','rb'))
bernoulli = pickle.load(open('bernoulli.pkl', 'rb'))
cv = pickle.load(open('cv.pkl', 'rb'))
global corrMatrix
corrMatrix = pd.read_csv('corrMatrix.csv')
my_api_key = 'fee15dbf316a148774d45f892bc49f4b';
moviesWithLinks=pd.read_csv("moviesWithLinks.csv")
rating=pd.read_csv("ratings.csv")
global links
links=pd.read_csv('links.csv')
global ratings
ratings=pd.merge(links,rating).drop(['movieId','timestamp','imdbId'],axis=1)
# global user
# user =ratings[ratings['userId']==3][['tmdbId','rating']]
# romanticUser=[[785539,5], [800669,5], [638449,5], [662237,5], [613504,5], [784500,5], [785537,5], [317442,5], [685274,5], [744275,5], [802504,5], [572154,5], [537915,4], [727745,5], [454983,5], [486589,5], [372058,5], [216015,5], [583083,5], [632632,5]]


global moviesGenres
moviesGenres= [{'id': 28, 'name': 'Action'}, {'id': 12, 'name': 'Adventure'}, {'id': 16, 'name': 'Animation'},
                {'id': 35, 'name': 'Comedy'}, {'id': 80, 'name': 'Crime'}, {'id': 99, 'name': 'Documentary'},
                {'id': 18, 'name': 'Drama'}, {'id': 10751, 'name': 'Family'}, {'id': 14, 'name': 'Fantasy'},
                {'id': 36, 'name': 'History'}, {'id': 27, 'name': 'Horror'}, {'id': 10402, 'name': 'Music'},
                {'id': 9648, 'name': 'Mystery'}, {'id': 10749, 'name': 'Romance'},
                {'id': 878, 'name': 'Science Fiction'},
                {'id': 10770, 'name': 'TV Movie'}, {'id': 53, 'name': 'Thriller'}, {'id': 10752, 'name': 'War'},
                ]


def get_similar(tmdbId,rating):
    tmdbId=tmdbId+".0"
    # print("calling get similar")
    # print("tmdb id is ", tmdbId)
    # print(type(tmdbId))
    # print( "matrix columns",corrMatrix.columns)
    if(tmdbId in corrMatrix.columns):
        print("tmdb id is ", tmdbId)
        print("tmdb is in corrMatrix")
        similar_ratings = corrMatrix[tmdbId]*(rating-2.5)
        similar_ratings = similar_ratings.sort_values(ascending=False)
        return similar_ratings
def collaborative_filtering(userId):
    userRatings = UserRating.query.filter_by(userId=userId).all()
    print("user rating fetch in coolaborative filtering",userRatings)
    # if (len(userRatings)>9):
    db.session.query(RecommendedMovie).filter(RecommendedMovie.userId == current_user.id).delete()
    db.session.commit()

    movieIds=[]
    similar_movies = pd.DataFrame()
    for userRating in userRatings:
        similar_movies = similar_movies.append(get_similar(str(userRating.movieId), userRating.rating), ignore_index=True)
        movieIds.append(userRating.movieId)
    # for movie in romanticUser:
    #     similar_movies = similar_movies.append(get_similar(str(movie[0]), movie[1]), ignore_index=True)
    print("similar movies are",similar_movies)
    relatedMovies = similar_movies.sum().sort_values(ascending=False).index.tolist()

    tmdbIds  = relatedMovies[0:8]
    tmdbTitles = []
    tmdbPosters=[]
    for i in tmdbIds:
        tmdbPoster, tmdbTitle = fetch_poster_and_title(i)
        tmdbTitles.append(tmdbTitle)
        tmdbPosters.append(tmdbPoster)
    if tmdbPosters and tmdbTitles:
        for i in range(0,10):
            if tmdbTitles[i] != 'not available':
                print("adding movies in recommended movie database",tmdbTitles[i])
                recommended_movies = RecommendedMovie(userId = userId,tmdbId = tmdbIds[i],tmdbTitle = tmdbTitles[i],tmdbPoster=tmdbPosters[i])
                db.session.add(recommended_movies)
                db.session.commit()

def fetch_poster(movie_id):
    # my_api_key = 'fee15dbf316a148774d45f892bc49f4b';
    # movie_id = str(movie_id)
    # data = requests.get('https://api.themoviedb.org/3/movie/' + movie_id + '?api_key=' + my_api_key)
    # data = json.loads(data.content)
    # poster = 'https://image.tmdb.org/t/p/original' + data['poster_path']
    # return poster
    my_api_key = 'fee15dbf316a148774d45f892bc49f4b';
    movie_id = str(movie_id)
    data = requests.get('https://api.themoviedb.org/3/movie/' + movie_id + '?api_key=' + my_api_key)
    poster = "not available"
    if (data):
        data = json.loads(data.content)
        if (data['poster_path']):
            poster = 'https://image.tmdb.org/t/p/original' + data['poster_path']
        else:
            poster = "not available"
    else:
        poster = "not available"
    return poster
def fetch_poster_and_title(movie_id):
    my_api_key = 'fee15dbf316a148774d45f892bc49f4b';
    movie_id = str(movie_id)
    data = requests.get('https://api.themoviedb.org/3/movie/' + movie_id + '?api_key=' + my_api_key)
    poster = "not available"
    title = "not available"
    if (data):
        data = json.loads(data.content)
        if (data['poster_path']):
            poster = 'https://image.tmdb.org/t/p/original' + data['poster_path']
        if data['title']:
            title=data['title']
    # print("title", title)
    # print("poster", poster)
    return poster, title
def getRecomendations(title):
    index = movies[movies['title'] == title]
    recommended_movie_names = []
    recommended_movie_posters = []
    recommended_movie_ids = []
    if (index.empty):
        return recommended_movie_ids, recommended_movie_names, recommended_movie_posters
    else:
        index=index.index[0]
        distances = sorted(list(enumerate(similarity[index])), reverse=True, key=lambda x: x[1])
        for i in distances[1:6]:
            # fetch the movie poster
            movie_id = movies.iloc[i[0]].movie_id
            recommended_movie_ids.append(movie_id)
            recommended_movie_posters.append(fetch_poster(movie_id))
            recommended_movie_names.append(movies.iloc[i[0]].title)

    return recommended_movie_ids, recommended_movie_names, recommended_movie_posters




def scrapReviews(imdbId):
    sauce = urllib.request.urlopen('https://www.imdb.com/title/{}/reviews?ref_=tt_ov_rt'.format(imdbId)).read()
    soup = bs.BeautifulSoup(sauce, 'lxml')
    soup_result = soup.find_all("div", {"class": "text show-more__control"})
    reviewsList = []  # list of reviews
    reviewsSentiment = []  # list of comments (good or bad)
    for reviews in soup_result:
        if reviews.string:
            reviewsList.append(reviews.string)
            # passing the review to our model
            movie_review_list = np.array([reviews.string])
            reviewVector = cv.transform(movie_review_list)
            pred = bernoulli.predict(reviewVector)
            reviewsSentiment.append('Good' if pred else 'Bad')

    # combining reviews and comments into a dictionary
    movieReviews = {reviewsList[i]: reviewsSentiment[i] for i in range(len(reviewsList))}
    return movieReviews

@app.route('/profile')
@login_required
def profile():
    userId=current_user.id
    print("current user is",userId)
    userRatings = UserRating.query.filter_by(userId=userId).all()
    # print("movie ids are",userRatings.movieId)
    if userRatings:
        titles=[]
        posters =[]
        for rating in userRatings:
            # print("rating",rating.id)
            p,t = fetch_poster_and_title(rating.movieId)
            posters.append(p)
            titles.append(t)

        return render_template('profile.html',titles=titles,posters=posters,userRatings=userRatings)
    else:
        return render_template('profile.html')
@app.route('/rate', methods=['POST'])
@login_required
def rate():
    userId=current_user.id
    movieId = request.json['movieId']
    rating = request.json['rating']
    # print(movieId)
    # print(rating)
    userRatings = UserRating.query.filter_by(userId=userId).all()
    if movieId and rating:
        for r in userRatings:
            print(movieId,r.movieId)

            if movieId == str(r.movieId):
                print("ratuing already present")
                r.rating=rating
                db.session.commit()
                collaborative_filtering(userId)

                return jsonify({'vote_rate': rating})
        print("ratuing already not present")

        new_rating = UserRating(userId=userId, movieId=movieId, rating=rating)
        db.session.add(new_rating)
        db.session.commit()
        collaborative_filtering(userId)

        return jsonify({'vote_rate': rating})
    else:
        resp = jsonify({'message': 'Bad Request - invalid credendtials'})
        resp.status_code = 400
        return resp
@app.route('/login')
def login():
    return render_template('login.html',moviesGenres=moviesGenres)

@app.route('/login', methods=['POST'])
def login_post():
    email = request.form.get('email')
    password = request.form.get('password')
    remember = True if request.form.get('remember') else False

    user = User.query.filter_by(email=email).first()

    if not user or not check_password_hash(user.password, password):
        flash('Please check your login details and try again.')
        return redirect(url_for('login'))

    login_user(user, remember=remember)

    return redirect(url_for('h'))

@app.route('/signup')
def signup():
    return render_template('signup.html',moviesGenres=moviesGenres)

@app.route('/signup', methods=['POST'])
def signup_post():
    email = request.form.get('email')
    name = request.form.get('name')
    password = request.form.get('password')

    user = User.query.filter_by(email=email).first()

    if user:
        flash('Email address already exists.')
        return redirect(url_for('login'))

    new_user = User(email=email, name=name, password=generate_password_hash(password, method='sha256'))

    db.session.add(new_user)
    db.session.commit()

    return redirect(url_for('login'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))
@app.route("/")
@app.route("/h")
def h():
    my_api_key = 'fee15dbf316a148774d45f892bc49f4b';
    tmdbPosters=[]
    tmdbTitles=[]
    tmdbIds=[]
    if(current_user.is_authenticated):
        userId=current_user.id
        print("authenticated")
        recommended_movies_data = RecommendedMovie.query.filter_by(userId=userId).all()
        if recommended_movies_data:
            print("data available")
            for movie in recommended_movies_data:
                print("recomended movie",movie.tmdbTitle)
                tmdbPosters.append(movie.tmdbPoster)
                tmdbTitles.append(movie.tmdbTitle)
                tmdbIds.append(movie.tmdbId)


    dailyTrending = requests.get('https://api.themoviedb.org/3/trending/movie/day?api_key=' + my_api_key)
    dailyTrending = dailyTrending.json()
    dailyTrending = dailyTrending['results']
    weeklyTrending = requests.get('https://api.themoviedb.org/3/trending/movie/week?api_key=' + my_api_key)
    weeklyTrending = weeklyTrending.json()
    weeklyTrending = weeklyTrending['results']

    popularMovies = requests.get('https://api.themoviedb.org/3/movie/popular?api_key=' + my_api_key)
    popularMovies = popularMovies.json()
    popularMovies = popularMovies['results']
    topRatedMovies = requests.get('https://api.themoviedb.org/3/movie/top_rated?api_key=' + my_api_key)
    topRatedMovies = topRatedMovies.json()
    topRatedMovies = topRatedMovies['results']
    latestMovies = requests.get('https://api.themoviedb.org/3/movie/latest?api_key=' + my_api_key)
    latestMovies = latestMovies.json()


    return render_template('home.html',data=" ",tmdbTitles=tmdbTitles,tmdbIds=tmdbIds,tmdbPosters=tmdbPosters, weeklyTrending=weeklyTrending,dailyTrending=dailyTrending, popularMovies=popularMovies,latestMovies=latestMovies,topRatedMovies=topRatedMovies,moviesGenres=moviesGenres)

@app.route("/home/<title>", methods=["GET","POST"])
def home(title):

    my_api_key = 'fee15dbf316a148774d45f892bc49f4b';


    data=requests.get('https://api.themoviedb.org/3/search/movie?api_key=' + my_api_key + '&query=' + title)
    data=json.loads(data.content)
    data=data['results']

    return render_template('home.html', data=data, moviesGenres=moviesGenres)

@app.route("/genre/<id>", methods=['GET', 'POST'])
def genre(id):
    my_api_key = 'fee15dbf316a148774d45f892bc49f4b';
    data = requests.get('https://api.themoviedb.org/3/discover/movie?api_key=fee15dbf316a148774d45f892bc49f4b&language=en-US&sort_by=popularity.desc&include_adult=false&include_video=false&page=1&with_genres='+id+'&with_watch_monetization_types=flatrate')
    data = json.loads(data.content)
    genresList = data['results']
    romanticUser=[]
    # for movieGenre in genresList:
    #     romanticUser.append(movieGenre['id'])
    # print(romanticUser)

    return render_template('home.html', data=" ", genresList=genresList,moviesGenres=moviesGenres)

@app.route("/recommend/<movieId>", methods=['GET', 'POST'])
def recommend(movieId):


    my_api_key = 'fee15dbf316a148774d45f892bc49f4b';
    data = requests.get('https://api.themoviedb.org/3/movie/'+movieId+'?api_key='+my_api_key)
    data = json.loads(data.content)
    movieI=data['id']
    # print("movieI is", movieI)
    title=data['title']
    imdbId = data['imdb_id']
    print("imdb id is",imdbId)
    poster ='https://image.tmdb.org/t/p/original'+ data['poster_path']
    genres = data['genres']
    overview = data['overview']
    vote_average =data['vote_average']
    vote_count =data['vote_count']
    release_date = data['release_date']
    runtime = data['runtime']
    status = data['status']
    reviews=scrapReviews(imdbId)
    # print("title is", data['title'])
    recommended_movie_ids, recommended_movie_names, recommended_movie_posters= getRecomendations(title)
    # print("name is",recommended_movie_names)
    # print("recommended movie ")


    return render_template('recommendation.html',movieI=movieI, title=title, poster=poster, overview=overview, vote_average=vote_average,
                           vote_count=vote_count, release_date=release_date, runtime=runtime, status=status, genres=genres, reviews=reviews, recommended_movie_names=recommended_movie_names, recommended_movie_posters= recommended_movie_posters, recommended_movie_ids= recommended_movie_ids,moviesGenres=moviesGenres)


if __name__ == '__main__':
    app.run(debug=True)