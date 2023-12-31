import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")

# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""

    stocks = db.execute("SELECT share_smbl, share_name, SUM(numFshares) FROM transactions WHERE user_id=? GROUP BY share_smbl",session["user_id"])
    totalWorth = 0
    for stock in stocks:
        stock["currentPrice"] = lookup(stock["share_smbl"])["price"]
        stock["total"] = stock["currentPrice"] * stock["SUM(numFshares)"]
        stock["numFshares"] = stock.pop("SUM(numFshares)")
        totalWorth += stock["total"]

    balance = db.execute("SELECT cash FROM users WHERE id = ?", session["user_id"])[0]["cash"]
    totalWorth += float(balance)


    # print(stocks)
    # print(balance)
    # print(totalWorth)

    return render_template("index.html", stocks = stocks, balance= balance, totalWorth = totalWorth)


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""

    if request.method == "POST":
        smbl = request.form.get("symbol")
        numShares = request.form.get("shares")

        try:
            if not smbl:
                return apology("Missing Symbol", 400)
            elif not numShares:
                return apology("Missing Shares", 400)
            elif float(numShares) <0 or (float(numShares)%1) != 0:
                return apology("Invalid entry", 400)
            elif lookup(smbl) == None:
                return apology("no such stock symbol exist", 400)
        except:
            return apology("error has happened", 400)

        balance = db.execute("SELECT cash FROM users WHERE id = ?", session["user_id"])
        share = lookup(smbl)
        shareTotal = float(numShares) * share["price"]
        cashRemaining = float(balance[0]["cash"]) - shareTotal

        if cashRemaining < 0:
            return apology("You don't have enough balance", 400)
        else:
            db.execute("INSERT INTO transactions (user_id, share_smbl, pricePshare, numFshares, time, total, share_name, type) VALUES(?, ?, ?, ?, ?, ?, ?, ?)",session["user_id"],share["symbol"],share["price"], numShares, datetime.now(), shareTotal, share["name"], "Purshased")
            db.execute("UPDATE users SET cash = ? WHERE id = ?",cashRemaining, session["user_id"])
            flash("Bought!")
            return redirect("/")
    else:
        return render_template("buy.html")


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""

    transactions = db.execute("SELECT share_smbl, share_name, numFshares, pricePshare, time FROM transactions WHERE user_id=? ORDER BY time",session["user_id"])

    return render_template("history.html", transactions=transactions)


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
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
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


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""

    if request.method == "POST":
        smbl = request.form.get("symbol")

        if not smbl:
            return apology("Missing Symbol", 400)
        elif lookup(smbl) == None:
            return apology("no such stock symbol exist", 400)
        else:
            return render_template("quoted.html",smbl=lookup(smbl))
    else:
        return render_template("quote.html")




@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    if request.method == "POST":
        session.clear()
        username = request.form.get("username").lower()
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        if not username:
            return apology("must provide username", 400)

        elif not password:
            return apology("must provide password", 400)

        elif not confirmation:
            return apology("must rewrite the password", 400)

        elif len(db.execute("SELECT * FROM users WHERE username = ?", username)) != 0:
            return apology("the username already exists", 400)

        if password != confirmation:
            return apology("the passwords do not match", 400)

        db.execute("INSERT INTO users (username, hash) VALUES (?,?)",username,generate_password_hash(password, salt_length=8))

        rows = db.execute("SELECT * FROM users WHERE username = ?", username)
        session["user_id"] = rows[0]["id"]

        # flash a confirmation
        flash("you are successfuly registered")

        return redirect("/")

    else:
        return render_template("register.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""

    if request.method == "POST":
        smbl = request.form.get("symbol")
        numShares = request.form.get("shares")

        if not smbl:
            return apology("Missing Symbol", 400)

        elif not numShares:
            return apology("Missing Shares", 400)

        elif int(numShares) <0 or (float(numShares)%1) != 0 :
            return apology("Invalid entry", 400)

        stocks = db.execute("SELECT share_smbl, share_name, SUM(numFshares) FROM transactions WHERE user_id=? AND share_smbl=? ",session["user_id"],smbl)

        if stocks[0]["SUM(numFshares)"] < int(numShares) :
            return apology("You don't have enough shares", 400)

        else:

            numShares = int(numShares)*-1
            print(type(numShares))
            print("numshares=",numShares,"shareName=",smbl)
            share = lookup(smbl)
            shareTotal = numShares * share["price"]
            balance = db.execute("SELECT cash FROM users WHERE id = ?", session["user_id"])
            cashRemaining = float(balance[0]["cash"]) - shareTotal
            db.execute("INSERT INTO transactions (user_id, share_smbl, pricePshare, numFshares, time, total, share_name, type) VALUES(?, ?, ?, ?, ?, ?, ?, ?)",session["user_id"],share["symbol"],share["price"],  numShares, datetime.now(), shareTotal, share["name"], "Sold")
            db.execute("UPDATE users SET cash = ? WHERE id = ?",cashRemaining, session["user_id"])
            flash("Sold!")
            return redirect("/")
    else:
        stocks = db.execute("SELECT share_smbl FROM transactions WHERE user_id=? GROUP BY share_smbl",session["user_id"])
        return render_template("sell.html",stocks=stocks)

