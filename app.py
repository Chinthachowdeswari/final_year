import sqlite3
from datetime import datetime
from database import connect_db, get_db
from flask import Flask, render_template, request, flash, redirect, g
import pickle
import numpy as np
from PIL import Image
from tensorflow.keras.models import load_model



app = Flask(__name__)

def connect_db():
    sql = sqlite3.connect('food_log.db')
    sql.row_factory = sqlite3.Row
    return sql

def get_db():
    if not hasattr(g,'sqlite3_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db

@app.teardown_appcontext
def close_db(error):
    if hasattr(g, 'sqlite3_db'):
        g.sqlite_db.close()

@app.route('/')
def home():
    return render_template('main1.html')

@app.route("/home", methods=['GET', 'POST'])
def home2():
    return render_template('home.html')

@app.route("/base", methods=['GET', 'POST'])
def basePage():
    return render_template('base.html')

@app.route('/home1', methods=['POST', 'GET'])
def index():
    db = get_db()
    if request.method == "POST":
        date = request.form['date']
        print(date)
        dt = datetime.strptime(date, '%Y-%m-%d')
        database_date = datetime.strftime(dt, '%Y%m%d')
        db.execute('insert into log_date (entry_date) values (:database_date)',
                           {'database_date': database_date})
        db.commit()

    cur = db.execute('''select log_date.entry_date, sum(food.protein) as protein,
                     sum(food.carbohydrates) as carbohydrates, 
                     sum(food.fat) as fat, 
                     sum(food.calories) as calories 
                     from log_date left join food_date on food_date.log_date_id = log_date.id 
                     left join food on food.id = food_date.food_id group by log_date.id order by log_date.entry_date desc''')
    results = cur.fetchall()

    date_results = []

    for i in results:
        single_date = {}

        single_date['entry_date'] = i['entry_date']
        single_date['carbohydrates'] = i['carbohydrates']
        single_date['fat'] = i['fat']
        single_date['calories'] = i['calories']

        d = datetime.strptime(str(i['entry_date']), '%Y%m%d')

        single_date['pretty_date'] = datetime.strftime(d, '%B %d, %Y')

        date_results.append(single_date)
    # print(pretty_results)
    return render_template('home1.html', results=date_results)


@app.route('/view/<date>', methods=['GET', 'POST'])  # date 20170520
def view(date):
    db = get_db()
    cur = db.execute('select id, entry_date from log_date where entry_date = :date', {'date': date})
    date_result = cur.fetchone()

    if request.method == 'POST':
        db.execute('insert into food_date (food_id, log_date_id) values (:food_id,:log_date_id)', \
                   {'food_id': request.form['food-select'], 'log_date_id': date_result['id']})
        db.commit()
        # return '<h1> The food item added is #{}'.format(request.form['food-select'])

    d = datetime.strptime(str(date_result['entry_date']), '%Y%m%d')
    pretty_date = datetime.strftime(d, '%B %d, %Y')

    food_cur = db.execute('select id, name from food')
    food_results = food_cur.fetchall()

    log_cur = db.execute('''select food.name,food.protein, food.carbohydrates, food.fat, food.calories 
                        from log_date join food_date on food_date.log_date_id = log_date.id 
                        join food on food.id = food_date.food_id where log_date.entry_date = :date''', {'date': date})
    log_results = log_cur.fetchall()

    totals = {}
    totals['protein'] = 0
    totals['carbohydrates'] = 0
    totals['fat'] = 0
    totals['calories'] = 0

    for food in log_results:
        totals['protein'] += food['protein']
        totals['carbohydrates'] += food['carbohydrates']
        totals['fat'] += food['fat']
        totals['calories'] += food['calories']

    return render_template('day.html', entry_date=date_result['entry_date'], pretty_date=pretty_date, \
                           food_results=food_results, log_results=log_results, totals=totals)


@app.route('/food', methods=['GET', 'POST'])
def food():
    db = get_db()
    if request.method == 'POST':
        name = request.form['food-name']
        protein = int(request.form['protein'])
        carbohydrates = int(request.form['carbohydrates'])
        fat = int(request.form['fat'])
        calories = protein * 4 + carbohydrates * 4 + fat * 9
        db.execute('''insert into food(name, protein, carbohydrates, fat, calories) 
        values (:name, :protein, :carbohydrates, :fat, :calories)''',
                   {'name': name, 'protein': protein, 'carbohydrates': carbohydrates, 'fat': fat, 'calories': calories})
        db.commit()

    cur = db.execute('select name, protein, carbohydrates, fat, calories from food')
    results = cur.fetchall()
    return render_template('add_food.html', results=results)


def predict(values, dic):
    if len(values) == 8:
        model = pickle.load(open('models/diabetes.pkl','rb'))
        values = np.asarray(values)
        return model.predict(values.reshape(1, -1))[0]
    elif len(values) == 26:
        model = pickle.load(open('models/breast_cancer.pkl','rb'))
        values = np.asarray(values)
        return model.predict(values.reshape(1, -1))[0]
    elif len(values) == 13:
        model = pickle.load(open('models/heart.pkl','rb'))
        values = np.asarray(values)
        return model.predict(values.reshape(1, -1))[0]
    elif len(values) == 18:
        model = pickle.load(open('models/kidney.pkl','rb'))
        values = np.asarray(values)
        return model.predict(values.reshape(1, -1))[0]
    elif len(values) == 10:
        model = pickle.load(open('models/liver.pkl','rb'))
        values = np.asarray(values)
        return model.predict(values.reshape(1, -1))[0]



@app.route("/diabetes", methods=['GET', 'POST'])
def diabetesPage():
    return render_template('diabetes.html')

@app.route("/cancer", methods=['GET', 'POST'])
def cancerPage():
    return render_template('breast_cancer.html')

@app.route("/heart", methods=['GET', 'POST'])
def heartPage():
    return render_template('heart.html')

@app.route("/kidney", methods=['GET', 'POST'])
def kidneyPage():
    return render_template('kidney.html')

@app.route("/liver", methods=['GET', 'POST'])
def liverPage():
    return render_template('liver.html')

@app.route("/malaria", methods=['GET', 'POST'])
def malariaPage():
    return render_template('malaria.html')

@app.route("/pneumonia", methods=['GET', 'POST'])
def pneumoniaPage():
    return render_template('pneumonia.html')

@app.route("/predict", methods = ['POST', 'GET'])
def predictPage():
    try:
        if request.method == 'POST':
            to_predict_dict = request.form.to_dict()
            to_predict_list = list(map(float, list(to_predict_dict.values())))
            pred = predict(to_predict_list, to_predict_dict)
    except:
        message = "Please enter valid Data"
        return render_template("home.html", message = message)

    return render_template('predict.html', pred = pred)

@app.route("/malariapredict", methods = ['POST', 'GET'])
def malariapredictPage():
    if request.method == 'POST':
        try:
            if 'image' in request.files:
                img = Image.open(request.files['image'])
                img = img.resize((36,36))
                img = np.asarray(img)
                img = img.reshape((1,36,36,3))
                img = img.astype(np.float64)
                model = load_model("models/malaria.h5")
                pred = np.argmax(model.predict(img)[0])
        except:
            message = "Please upload an Image"
            return render_template('malaria.html', message = message)
    return render_template('malaria_predict.html', pred = pred)

@app.route("/pneumoniapredict", methods = ['POST', 'GET'])
def pneumoniapredictPage():
    if request.method == 'POST':
        try:
            if 'image' in request.files:
                img = Image.open(request.files['image']).convert('L')
                img = img.resize((36,36))
                img = np.asarray(img)
                img = img.reshape((1,36,36,1))
                img = img / 255.0
                model = load_model("models/pneumonia.h5")
                pred = np.argmax(model.predict(img)[0])
        except:
            message = "Please upload an Image"
            return render_template('pneumonia.html', message = message)
    return render_template('pneumonia_predict.html', pred = pred)

if __name__ == '__main__':
	app.run(debug = True)