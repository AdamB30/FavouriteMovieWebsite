from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Float
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
import requests

API_READ_ACCESS_TOKEN = "Bearer eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiJlN2FhYjU5MWE5MzJmZDQyYmQ4MjViMDEwYzgwMmJmZSIsIm5iZiI6MTc0ODAxNTUxNC40MjU5OTk5LCJzdWIiOiI2ODMwOTk5YWE2NGRhMDQzNDZiNmE5YWIiLCJzY29wZXMiOlsiYXBpX3JlYWQiXSwidmVyc2lvbiI6MX0.xNoSxHOnC8MC20vNrEEkQ--m1wkkYDa39lT4Nrc-K1E"
API_KEY = "e7aab591a932fd42bd825b010c802bfe"
API_SEARCH_URL = "https://api.themoviedb.org/3/search/movie"
API_DETAILS_URL = "https://api.themoviedb.org/3/movie"
MOVIE_DB_IMAGE_URL = "https://image.tmdb.org/t/p/w500"
header = {'accept': "application/json", 'Authorization': API_READ_ACCESS_TOKEN}

class MovieRateForm(FlaskForm):
    rating = StringField('Your rating out of 10 e.g. 7.5', validators=[DataRequired()])
    review = StringField('Your Review', validators=[DataRequired()])
    submit = SubmitField('Update')

class AddMovieForm(FlaskForm):
    title = StringField('Movie Title', validators=[DataRequired()])
    submit = SubmitField('Add Movie')

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///movie-ranking.db"
Bootstrap5(app)

# CREATE DB
class Base(DeclarativeBase):
  pass

db = SQLAlchemy(model_class= Base)
db.init_app(app)

class Movie(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key= True)
    title: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    year: Mapped[int] = mapped_column(Integer,nullable= False)
    description: Mapped[str] = mapped_column(String, nullable= False)
    rating: Mapped[int] = mapped_column(Integer, nullable= True)
    ranking: Mapped[int] = mapped_column(Integer, nullable= True)
    review: Mapped[str] = mapped_column(String, nullable= True)
    img_url: Mapped[str] = mapped_column(String, nullable= False)

    def __repr__(self):
        return f"<Movie {self.title}"

new_movie = Movie(
    title="Phone Booth",
    year=2002,
    description="Publicist Stuart Shepard finds himself trapped in a phone booth, pinned down by an extortionist's sniper rifle. Unable to leave or receive outside help, Stuart's negotiation with the caller leads to a jaw-dropping climax.",
    rating=7.3,
    ranking=10,
    review="My favourite character was the caller.",
    img_url="https://image.tmdb.org/t/p/w500/tjrX2oWRCM3Tvarz38zlZM7Uc10.jpg")
second_movie = Movie(
    title="Avatar The Way of Water",
    year=2022,
    description="Set more than a decade after the events of the first film, learn the story of the Sully family (Jake, Neytiri, and their kids), the trouble that follows them, the lengths they go to keep each other safe, the battles they fight to stay alive, and the tragedies they endure.",
    rating=7.3,
    ranking=9,
    review="I liked the water.",
    img_url="https://image.tmdb.org/t/p/w500/t6HIqrRAclMCA60NsSmeqe9RmNV.jpg"
)

# CREATE TABLE
with app.app_context():
    db.create_all()

@app.route("/")
def home():
    result= db.session.execute(db.select(Movie).order_by(Movie.rating))
    all_movies = result.scalars().all()
    for i in range(len(all_movies)):
        all_movies[i].ranking = len(all_movies) - i
    return render_template("index.html", all_movies= all_movies)

@app.route("/edit/<movie>", methods= ["GET", "POST"])
def edit(movie):
    form = MovieRateForm()
    edit_movie = db.session.execute(db.select(Movie).where(Movie.title == movie)).scalar()
    if request.method == "GET":
        return render_template("edit.html", movie= edit_movie, form= form)
    else:
        if form.validate_on_submit():
            edit_movie.rating = request.form['rating']
            edit_movie.review = request.form['review']
            db.session.commit()
            return redirect(url_for('home'))
        else:
            return render_template("edit.html", movie=edit_movie, form=form)

@app.route('/delete/<movie>')
def delete(movie):
    del_movie = db.session.execute(db.select(Movie).where(Movie.title == movie)).scalar()
    db.session.delete(del_movie)
    db.session.commit()
    return redirect(url_for('home'))

@app.route('/add', methods= ["GET", "POST"])
def add():
    form= AddMovieForm()
    if request.method == "GET":
        return render_template('add.html', form= form)
    else:
        if form.validate_on_submit():
            search_params= {'query': request.form['title']}
            response = requests.get(API_SEARCH_URL, params= search_params, headers= header)
            data = response.json()
            print(data['results'])
            return render_template('select.html', movie_data= data['results'])
        else:
            return render_template("add.html", form=form)

@app.route('/find')
def find_info():
    movie = request.args.get('id')
    response = requests.get(f'{API_DETAILS_URL}/{movie}', headers= header)
    data = response.json()
    new_movie = Movie(title= data['original_title'],
                      year= data['release_date'][0:4],
                      description= data['overview'],
                      img_url= f"{MOVIE_DB_IMAGE_URL}{data['poster_path']}")
    db.session.add(new_movie)
    db.session.commit()
    return redirect(url_for('edit', movie= new_movie.title))


if __name__ == '__main__':
    app.run(debug=True)

