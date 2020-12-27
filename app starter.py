# Brittany Rollins
# Fall 2020
# sect 31854
# Final Project

from random import random
from countryinfo import CountryInfo
import requests
from flask import Flask, redirect, render_template, request, session, url_for
import os
import sqlite3 as sl
import pandas as pd
import matplotlib.pyplot as plt
import io
from sklearn.linear_model import LinearRegression
import pycountry
import numpy as np
from datetime import date
import math
import ccy


app = Flask(__name__)
# database for confirmed cases


# path = /api/coronavirus/Japan/confirmed
# /api/coronavirus/<country_name>/confirmed 
# def confirmed(country_name): 
# not sure app route is right


@app.before_request
def make_session_permanent():
    session.permanent = True


@app.route("/")
def home():
    update_data()  # get most recent version of data
    return render_template('home.html')


@app.route('/action/goto', methods=['POST'])
def goto():
    session["country"] = request.form["country"]
    typ = request.form["type"]
    return redirect(url_for(typ, country=session["country"]))


@app.route('/api/coronavirus/confirmed/<string:country>/')
def confirmed(country):
    # get dictionary of confirmed cases and graph them
    c = get_cases_conf("new_confirmed.db", country)
    if c:
        fact = get_facts(country) # get fun facts for country
        x, y = zip(*sorted(c.items()))
        plt.plot(x, y)
        axes = plt.gca()
        axes.set_ylim([0, None])
        # save figure to an image to display on webpages
        img_name = 'images/' + country + 'c.png'
        plt.savefig('static/' + img_name)
        plt.close()
        return render_template('main_conf.html', country=country.capitalize(), facts = fact, cases=c, graph=img_name)
    else:  # default country, if no country in list that matches user input
        c = get_cases_conf("new_confirmed.db", "canada")
        x, y = zip(*sorted(c.items()))
        plt.plot(x, y)
        # save figure to an image to display on webpages
        img_name = 'images/canadac.png'
        plt.savefig('static/' + img_name)
        plt.close()
        return render_template('main_error.html', country="Canada", error_country=country.capitalize(), cases=c, graph=img_name)


@app.route('/api/coronavirus/recovered/<string:country>/')
def recovered(country):
    # get dictionary of confirmed cases and graph them
    c = get_cases_recov("new_recovered.db", country)
    if c:
        fact = get_facts(country) #get fun facts for country
        x, y = zip(*sorted(c.items()))
        plt.plot(x, y)
        axes = plt.gca()
        axes.set_ylim([0, None])
        # save figure to an image to display on webpages
        img_name = 'images/' + country + 'r.png'
        plt.savefig('static/' + img_name)
        plt.close()
        return render_template('main_recov.html', country=country.capitalize(), facts=fact, cases=c, graph=img_name)
    else:  # default country, no country in list that matches user input
        c = get_cases_recov("new_recovered.db", "canada")
        x, y = zip(*sorted(c.items()))
        plt.plot(x, y)
        # save figure to an image to display on webpages
        img_name = 'images/canadar.png'
        plt.savefig('static/' + img_name)
        plt.close()
        return render_template('main_error.html', country="Canada as default", error_country=country.capitalize(), cases=c, graph=img_name)


@app.route('/api/coronavirus/confirmed/projection/<string:country>/', methods=['GET'])
def predict_confirmed(country):
    session["country"] = country
    # get data to display from query parameters that were sent from form submission
    date = request.args.get('date')
    days = request.args.get('days')
    graph_name = request.args.get('graph')
    print('what was passed is ' + str(date) + str(days) + str(graph_name))
    return render_template('predictconf.html', country=country.capitalize(), date=date, days=days, graph=graph_name)


@app.route('/action/getdateconf', methods=['POST'])
def getdateconf():
    country = session["country"]
    if request.method == "POST":
        if request.form["date"] is not '':
            c = get_cases_recov("new_recovered.db", country)
            x, y = zip(*sorted(c.items()))
            x_pred = x[-30:]
            y_pred = y[-30:]
            dt = request.form["date"]
            dat = dt
            dt = dt.split('-')
            yr = int(dt[0])
            m = int(dt[1])
            dy = int(dt[2])
            pred = input_data(x_pred, y_pred, yr, m, dy)
            graph_name = create_pred_graph(x, y, dat, country, pred)
            print(str(dat) + ' ' + str(pred) + ' ' + str(graph_name))
        return redirect(url_for('predict_confirmed', country=country, date=dat, days=pred, graph=graph_name))


@app.route('/api/coronavirus/recovered/projection/<string:country>/', methods=['GET'])
def predict_recovered(country):
    session["country"] = country
    # get data needed to display on page from query parameters that were sent from form submission
    date = request.args.get('date')
    days = request.args.get('days')
    graph_name = request.args.get('graph')
    return render_template('predictrecov.html', country=country.capitalize(), date=date, days=days, graph=graph_name)


@app.route('/action/getdaterecov/', methods=['POST'])
def getdaterecov():
    country = session["country"]
    if request.method == "POST":
        if request.form["date"] is not '':
            c = get_cases_recov("new_recovered.db", country)
            x, y = zip(*sorted(c.items()))
            x_pred = x[-30:]
            y_pred = y[-30:]
            dt = request.form["date"]
            dat = dt
            dt = dt.split('-')
            yr = int(dt[0])
            m = int(dt[1])
            dy = int(dt[2])
            pred = input_data(x_pred, y_pred, yr, m, dy)
            graph_name = create_pred_graph(x, y, dat, country, pred)
        return redirect(url_for('predict_recovered', country=country, date=dat, days=pred, graph=graph_name))


# add new prediction data to arrays in order to creat graph of projection
def create_pred_graph(x, y, dt, country, pred):
    dt = dt.split('-')
    yr = int(dt[0])
    m = int(dt[1])
    dy = int(dt[2])
    x = list(x)
    y = list(y)
    x.append(get_days(yr, m, dy))
    y.append(pred)
    plt.plot(x, y)
    axes = plt.gca()
    axes.set_ylim([0, None])
    # save figure to an image to display on webpages
    r = random()
    img_name = 'images/' + country + str(r) + 'pred.png'
    plt.savefig('static/' + img_name)
    plt.close()
    return img_name


# get number of days between jan 22 2020 and user input date
def get_days(yr, mm, dd):
    d1 = date(2020, 1, 22)
    d2 = date(yr, mm, dd)
    num_days = d2 - d1
    # print(num_days.days)
    return num_days.days


# get prediction from user input of date
def input_data(x, y, yr, m, d):
    x = [[x_it] for x_it in x]
    y = [[y_it] for y_it in y]
    print(x)
    print(y)
    linreg = LinearRegression()
    linreg.fit(x, y)
    pred = linreg.predict([[get_days(yr, m, d)]])
    return math.ceil(pred)


#get country facts from pycountry and countryinfo
def get_facts(country):
    country_id2, country_id3, off_name = '', '', ''
    for co in list(pycountry.countries):
        if country.capitalize() in co.name:
            if hasattr(co, 'alpha_2'):
                country_id2 = co.alpha_2
            if hasattr(co, 'alpha_3'):
                country_id3 = co.alpha_3
            if hasattr(co, 'official_name'):
                off_name = co.official_name
    fact = ''
    pop_count = CountryInfo(country.capitalize())
    try:
        pop = pop_count.population()
    except KeyError:
        pop = ''
    if ccy.countryccy(country_id2.lower()) == None and ccy.countryccy(country_id3.lower()) == None:
        if off_name:
            fact += "Some facts about this country are that its official name is " + off_name
        if fact == '':
            return "No fact could be found"
    else:
        currency = ccy.countryccy(country_id2.lower())
        if currency == None:
            currency = ccy.countryccy(country_id3.lower())
        fact = "Some facts about this country are that the nation's currency is " + currency
        if off_name:
            fact += " and its official name is " + off_name
    if pop is not '':
        fact+=" and its population is " + str(pop) + " people"
    return fact


####Database functions code
def show_tbl_confirmed(conn):
    cur = conn.cursor()
    cur.execute("SELECT * FROM new_confirmed")
    rows = cur.fetchall()


def show_tbl_recovered(conn):
    cur = conn.cursor()
    cur.execute("SELECT * FROM new_recovered")
    rows = cur.fetchall()


#update data up to current data table
def update_data():
    # downloading confirmed data from github
    confirm_url = "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_confirmed_global.csv"  # Make sure the url is the raw version of the file on GitHub
    download = requests.get(confirm_url).content
    # Reading the downloaded content and turning it into a pandas dataframe
    df_conf = pd.read_csv(io.StringIO(download.decode('utf-8')))
    conn = sl.connect("new_confirmed.db")
    # delete table so to_sql can create a new one with updated columns
    conn.execute("DROP TABLE new_confirmed")
    df_conf.to_sql("new_confirmed", con=conn, if_exists='replace')

    # downloading recovered data from github
    recov_url = "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_recovered_global.csv"  # Make sure the url is the raw version of the file on GitHub
    download = requests.get(recov_url).content
    # Reading the downloaded content and turning it into a pandas dataframe
    df_recov = pd.read_csv(io.StringIO(download.decode('utf-8')))
    conn2 = sl.connect("new_recovered.db")
    #delete table so to_sql can create a new one with updated columns
    conn2.execute("DROP TABLE new_recovered")
    df_recov.to_sql("new_recovered", con=conn2, if_exists='replace')


def get_cases_conf(db, country):
    # correct string to proper case before looking in database
    country = country.lower()
    country = country.capitalize()
    conn = sl.connect(db, check_same_thread=False)
    cur = conn.cursor()
    get_country = "SELECT * FROM new_confirmed WHERE \"Country/Region\"=?"
    cur.execute(get_country, (country,))
    rows = cur.fetchall()

    cases_per_day = {}
    # code to add up cases from each region in country based on day and add to dictionary
    row_count = 0
    for row in rows:
        col_count = 0
        for col in row:
            if row_count == 0:
                if col_count > 4:
                    cases_per_day[col_count - 5] = col
                col_count += 1
            else:
                if col_count > 4:
                    cases_per_day[col_count - 5] += col
                col_count += 1
        row_count += 1
    return cases_per_day


def get_cases_recov(db, country):
    # correct string to proper case before looking in database
    country = country.lower()
    country = country.capitalize()
    conn = sl.connect(db, check_same_thread=False)
    cur = conn.cursor()
    get_country = "SELECT * FROM new_recovered WHERE \"Country/Region\"=?"
    cur.execute(get_country, (country,))
    rows = cur.fetchall()

    cases_per_day = {}
    # code to add up cases from each region in country based on day and add to dictionary
    row_count = 0
    for row in rows:
        col_count = 0
        for col in row:
            if row_count == 0:
                if col_count > 4:
                    cases_per_day[col_count - 5] = col
                col_count += 1
            else:
                if col_count > 4:
                    cases_per_day[col_count - 5] += col
                col_count += 1
        row_count += 1
    return cases_per_day


if __name__ == "__main__":

    app.secret_key = os.urandom(12)
    app.run(debug=True)
