#from flask import Flask, redirect, url_for, render_template


#app = Flask(__name__)


#@app.route("/")
#def home():
#    return render_template("index.html")

#if __name__ == "__main__":
#    app.run()

from website import create_app

app = create_app()

if __name__ =='__main__':
    app.run()