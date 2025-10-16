from flask import Flask, render_template, request, jsonify, redirect, url_for
import requests, sqlite3, time

app = Flask(__name__)
KEY = "0716289f2e856a66748b0ec8098ed8ec"

def db():
    con = sqlite3.connect("weather.db")
    c = con.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS cache(city TEXT PRIMARY KEY, data TEXT, t INTEGER)")
    c.execute("CREATE TABLE IF NOT EXISTS fav(id INTEGER PRIMARY KEY AUTOINCREMENT, city TEXT)")
    con.commit()
    con.close()

db()

def wdata(city):
    con = sqlite3.connect("weather.db")
    c = con.cursor()
    c.execute("SELECT data,t FROM cache WHERE city=?", (city,))
    r = c.fetchone()
    if r:
        d, t = r
        if time.time() - t < 600:
            con.close()
            return eval(d)

    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={KEY}&units=metric"
    res = requests.get(url)
    if res.status_code == 200:
        data = res.json()
        c.execute("REPLACE INTO cache(city,data,t) VALUES(?,?,?)", (city, str(data), int(time.time())))
        con.commit()
        con.close()
        return data
    con.close()
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
    con = sqlite3.connect("weather.db")
    c = con.cursor()
    c.execute("SELECT city FROM fav")
    favs = [x[0] for x in c.fetchall()]
    con.close()
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
    con = sqlite3.connect("weather.db")
    c = con.cursor()
    c.execute("INSERT OR IGNORE INTO fav(city) VALUES(?)", (city,))
    con.commit()
    con.close()
    return redirect(url_for('home'))

@app.route('/fav/del/<city>')
def fdel(city):
    con = sqlite3.connect("weather.db")
    c = con.cursor()
    c.execute("DELETE FROM fav WHERE city=?", (city,))
    con.commit()
    con.close()
    return redirect(url_for('home'))

 
@app.route('/city/<city>')
def city_weather(city):
    info = wdata(city)
    msg = ''
    if not info:
        msg = "City not found"
    con = sqlite3.connect("weather.db")
    c = con.cursor()
    c.execute("SELECT city FROM fav")
    favs = [x[0] for x in c.fetchall()]
    con.close()
    return render_template('index.html', weather=info, error=msg, favs=favs)

if __name__ == "__main__":
    app.run(debug=True)