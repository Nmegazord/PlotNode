import sqlite3
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

# Jumpingrivers imports
from pandas import read_csv
import plotly.express as px
from plotly.utils import PlotlyJSONEncoder
import json
import numpy as np

# Our own functions
from helpers import apology, login_required

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure SQLite database according to https://docs.python.org/3/library/sqlite3.html
conn = sqlite3.connect('user_data.db', check_same_thread=False)
db = conn.cursor()

@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""

    apology("TODO", 403)


    # # Get a portfolio from the database of what the user owns
    # portfolio = db.execute(
    #     "SELECT symbol, SUM(shares) FROM ledger WHERE user_id = :user_id GROUP BY symbol  HAVING SUM(shares) != 0", user_id=session["user_id"])

    # if not portfolio:
    #     # Calculate available cash
    #     cash = db.execute("SELECT cash FROM users WHERE id = :user_id", user_id=session["user_id"])[0]['cash']
    #     portfolio = list()
    #     portfolio.append(dict.fromkeys(['symbol', 'Name', 'SUM(shares)', 'Price', 'TOTAL']))
    #     return render_template("index.html", portfolio=portfolio, cash=cash, total=cash)

    # # Lookup the symbol and add missing data to the dictionary
    # for row in portfolio:
    #     lookup_result = lookup(row.get('symbol'))
    #     row['Name'] = lookup_result["name"]
    #     row['Price'] = lookup_result["price"]
    #     row['TOTAL'] = row.get('SUM(shares)') * lookup_result["price"]

    #     # Reorder dictionary
    #     for key in ['symbol', 'Name', 'SUM(shares)', 'Price', 'TOTAL']:
    #         row[key] = row.pop(key)

    # # Calculate available cash
    # cash = db.execute("SELECT cash FROM users WHERE id = :user_id", user_id=session["user_id"])[0]['cash']

    # # Calculate total of stocks + cash
    # total = 0
    # for row in portfolio:
    #     total += row.get('TOTAL')
    # total += cash

    # # Render results
    # return render_template("index.html", portfolio=portfolio, cash=cash, total=total)

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        username = (request.form.get("username"))
        rows = db.execute("SELECT * FROM users WHERE username = ?", (username,))
        results = rows.fetchall()
        print(results)
        print(results[0][2])
        print(results[0][1])

        # Ensure username exists and password is correct
        if len(results) != 1 or not check_password_hash(results[0][2], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = results[0][1]

        # Redirect user to home page
        flash('Welcome!')
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/pwdchange", methods=["GET", "POST"])
def pwdchange():
    """Change password"""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("old_password"):
            return apology("must insert current password", 403)

        # Ensure password was submitted
        elif not request.form.get("new_password"):
            return apology("must provide a new password", 403)

        # Ensure password was repeated
        elif not request.form.get("confirmation"):
            return apology("must confirm new password", 403)

        # Check if the confirmation password matches
        if request.form.get("new_password") != request.form.get("confirmation"):
            return apology("passwords need to match", 403)

        # Query database for personal data
        rows = db.execute("SELECT * FROM users WHERE id = :user_id", user_id=session["user_id"])

        # Ensure username exists and password is correct
        if not check_password_hash(rows[0]["hash"], request.form.get("old_password")):
            return apology("invalid password", 403)

        # Insert new one into the database
        else:
            db.execute("UPDATE users SET hash=:new_hash WHERE id = :user_id",
                       new_hash=generate_password_hash(request.form.get("new_password")), user_id=session["user_id"])

        # Redirect user to index
        flash('Password updated!')
        return redirect("/")

    # Redirect user to login form
    else:
        return render_template("pwdchange.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Ensure password was repeated
        elif not request.form.get("confirmation"):
            return apology("must confirm password", 403)

        # Check if the confirmation password matches
        if request.form.get("password") != request.form.get("confirmation"):
            return apology("passwords need to match", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username is new
        if len(rows) != 0:
            return apology("username already in use", 403)

        # Insert username and hash into the database
        else:
            db.execute("INSERT INTO users (username, hash) VALUES (:username, :pwd_hash)",
                       username=request.form.get("username"), pwd_hash=generate_password_hash(request.form.get("password")))

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Remember which user has registered and log him in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        flash('Registration successful!')
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)