from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_mysqldb import MySQL # type: ignore
import requests, time

app = Flask(__name__)
KEY = "0716289f2e856a66748b0ec8098ed8ec"

 
app.config['MYSQL_HOST'] = '127.0.0.1'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''      
app.config['MYSQL_DB'] = 'weather_db'     
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

mysql = MySQL(app)
 
def wdata(city):
    cur = mysql.connection.cursor()
    cur.execute("SELECT temp, weather, humidity, t FROM Cache WHERE city = %s", [city])
    r = cur.fetchone()
 
    if r and (time.time() - r['t'] < 600):
        cur.close()
        return {
            "name": city,
            "main": {"temp": r['temp'], "humidity": r['humidity']},
            "weather": [{"description": r['weather']}]
        }

    
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={KEY}&units=metric"
    res = requests.get(url)
    if res.status_code == 200:
        data = res.json()
        temp = data['main']['temp']
        hum = data['main']['humidity']
        weather_desc = data['weather'][0]['description']
        t = int(time.time())

         
        cur.execute("REPLACE INTO Cache(city, temp, weather, humidity, t) VALUES(%s, %s, %s, %s, %s)",
                    (city, temp, weather_desc, hum, t))
        mysql.connection.commit()
        cur.close()
        return data

    cur.close()
    return None

 
@app.route('/', methods=['GET', 'POST'])
def home():
    info, msg = None, ''
    if request.method == 'POST':
        city = request.form.get('city')
        if city:
            info = wdata(city)
            if not info:
                msg = "city not found"

    cur = mysql.connection.cursor()
    cur.execute("SELECT city FROM fav")
    favs = [x['city'] for x in cur.fetchall()]
    cur.close()
    return render_template('index.html', weather=info, error=msg, favs=favs)

 
@app.route('/api/<city>')
def api(city):
    d = wdata(city)
    if d:
        return jsonify({
            "city": d["name"],
            "temp": d["main"]["temp"],
            "desc": d["weather"][0]["description"],
            "hum": d["main"]["humidity"]
        })
    return jsonify({"error": "not found"}), 404
 
@app.route('/fav/add/<city>')
def fadd(city):
    cur = mysql.connection.cursor()
    cur.execute("INSERT IGNORE INTO fav(city) VALUES(%s)", [city])
    mysql.connection.commit()
    cur.close()
    return redirect(url_for('home'))

 
@app.route('/fav/del/<city>')
def fdel(city):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM fav WHERE city = %s", [city])
    mysql.connection.commit()
    cur.close()
    return redirect(url_for('home'))

 
@app.route('/city/<city>')
def city_weather(city):
    info = wdata(city)
    msg = ''
    if not info:
        msg = "City not found"
    cur = mysql.connection.cursor()
    cur.execute("SELECT city FROM fav")
    favs = [x['city'] for x in cur.fetchall()]
    cur.close()
    return render_template('index.html', weather=info, error=msg, favs=favs)

if __name__ == "__main__":
    app.run(debug=True)