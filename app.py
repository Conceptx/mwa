""" Microfinance Web Application by Theophilus Chidiebere Okoye """

#imports
import os
import pandas as pd
import numpy as np
import sqlite3 as sql
import re
from datetime import date, timedelta
from flask import Flask, redirect, render_template, request, url_for, session, flash
from functools import wraps

#configurations
app = Flask(__name__)
Flask.secret_key = '\xdf{\x85\xe8\xfe&\x0f\xc3\x17\xbc1b'
app.config['SECRET_KEY'] = '\xdf{\x85\xe8\xfe&\x0f\xc3\x17\xbc1b'
app.config['SQLALCHEMY_DATABASE-URI'] = 'sqlie:///' + os.getcwd() + 'static/Loan Profiles.db'
dbpath = 'static/Loan Profiles.db'

#global variables
username = ""
ccindex = 0


#unrouted functions

def update(name, paid, ltype):

    #Queries
    userid = getID(name, "CREDENTIALS")
    loanid = getID(ltype, "PAYMENT")

    Uquery = "UPDATE PAYMENTRECORDS SET PAID = PAID + '{0}' WHERE USERID = {1} ".format(paid, userid)
    Pquery = "UPDATE PAYMENT SET BALANCE = BALANCE - '{0}', TOTALPAID = TOTALPAID + '{0}' WHERE LOANID = {}".format(loanid)
    Lquery = "UPDATE LOANTYPE SET AVAILABLE = AVAILABLE - '{0}' WHERE TYPE = '{1}'".format(paid, ltype)

    #DB connect

    con = sql.connect(dbpath)
    cur = con.cursor()

    try:
        cur.execute(Uquery)
        cur.execute(Pquery)
        cur.execute(Lquery)

        con.commit()

    except:
        pass

    finally:
        con.close()

def getID(username, table):

    con = sql.connect(dbpath)
    cur = con.cursor()

    if table == "CREDENTIALS":
        query = "SELECT USERID FROM '{0}' WHERE USERNAME = '{1}'".format(table, username)
    if table == "PAYMENT":
        query = "SELECT LOANID FROM '{0}' WHERE USERNAME = '{1}'".format(table, username)

    cur.execute(query)
    rows = cur.fetchall()
    con.close()

    userid = 0

    for row in rows:
        userid = row[0]
    return userid

def instalment(interest , amount):

    userid = getID(username, "CREDENTIALS")

    #new query
    mtp = 0
    con = sql.connect(dbpath)
    cur = con.cursor()
    query = "SELECT MTP FROM LOANTYPE WHERE INTEREST = '{}'".format(interest)
    cur.execute(query)
    rows = cur.fetchall()

    for row in rows:
        mtp = row[0]
    con.close()

    rate = (interest / 12)/100
    instalment = amount * (rate * (1+rate)**mtp)/((1+rate)**mtp-1)

    return instalment

def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash("Requires login")
            return redirect(url_for('login'))

    return wrap


#routed functions

#404 page
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


#homepage
@app.route('/')
@app.route('/home')
def home():
    return render_template('home.html')



#signup
@app.route('/signup', methods=['GET', 'POST'])
def signup():

    con = sql.connect(dbpath)
    cur = con.cursor()

    try:
        #retrieving form data
        if request.method == 'GET':
           username = request.form.get('username')
           email = request.form.get('email')
           password = request.form.get('password')

        elif request.method == 'POST':
           username = request.form.get('username')
           email = request.form.get('email')
           password = request.form.get('password')

        #inserting to database
        if username != None or email != None or password != None:

            query = """UPDATE CREDENTIALS
                       SET USERNAME = '{0}', PASSWORD = '{1}', EMAIL = '{2}'
                       WHERE EMAIL = '{2}';
                    """.format(username, password, email)

            cur.execute(query)
            con.commit()
            con.close()
            return redirect(url_for('login'))

    except Exception as e:

        con.rollback()
        con.close
        raise e

    return render_template('signup.html')

#login
@app.route('/login', methods=['GET', 'POST'])
def login():

    verified = False
    global username
    error = " "

    con = sql.connect(dbpath)
    cur = con.cursor()


    try:
        #retrieving form data
        if request.method == 'GET':
            username = request.args.get('username')
            password = request.args.get('password')

        elif request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')

        #querying and password authentication


        query = "SELECT * FROM CREDENTIALS WHERE USERNAME = '{0}'".format(username)
        cur.execute(query)
        all_rows = cur.fetchall()


        for row in all_rows:
            dbUsername = row[0]
            dbPassword = row[1]
            dbRole = row[-2]

            if dbUsername == username:
                if password == dbPassword:
                    verified = True

        if verified == True and dbRole != 'ADMIN':
            return render_template('userportal.html', username=username)
        elif verified == True and dbRole == 'ADMIN':
            return render_template('adminportal.html', username=username)
        else:
            return render_template('login.html', error = 'Invalid Username and Password combination')

    except Exception as e:
        raise e

    finally:
        con.close()

    return render_template('login.html', error = error)

#user portal
@app.route('/portal')
@login_required
def portal():
    return render_template('userportal.html', username = username)

@app.route('/details')
def clientDetails():

    con = sql.connect(dbpath)
    cur = con.cursor()
    i = 0

    try:
        query = "SELECT USERNAME, SURNAME, NATIONALID, ADDRESS, CONTACT, EMAIL FROM CREDENTIALS WHERE USERNAME = '{}'".format(username)

        cur.execute(query)
        rows = cur.fetchall()

        df = pd.DataFrame(rows)
        df.columns = ['Name', 'Surname', 'ID', 'Address', 'Contact', 'Email']
        check = False

        while check == False:

            path = 'templates/details/info' +  str(i)  + '.html'
            file = 'details/info' + str(i) + '.html'
            if os.path.exists(path):
                check = False
                i += 1
            else:
                check = True


        df.to_html(path)
        html = ""
        with open(path, 'r') as myfile:
            html = myfile.read()

        pattern = r"right".format(html)
        html = re.sub(pattern, "left", html)
        with open(path, 'w') as myfile:
            myfile.write('''{% extends "userportal.html" %}
                            {% block details %}
                            ''')
        with open(path, 'a') as myfile:
            myfile.write("<style> tr{color: black;} </style>")
            myfile.write(html)
            myfile.write('{% endblock %}')

        return render_template(file, username = username)

    except Exception as e:
        raise e

    finally:
        con.close()


@app.route('/history')
def history():

    #connection
    con = sql.connect(dbpath)
    cur = con.cursor()
    i = 0
    userid = getID(username, "CREDENTIALS")
    try:

        query = ''' SELECT PAYMENTID, PAYMENTDATE, LOAN.LOANID, AMOUNT, LOANTYPE, PAID FROM PAYMENTRECORDS INNER JOIN LOAN ON PAYMENTRECORDS.USERID = LOAN.USERID WHERE LOAN.USERID = {} '''.format(userid)

        cur.execute(query)
        rows = cur.fetchall()


        df = pd.DataFrame(rows)
        df.columns = ['Payment #', 'Payment Date', 'Loan ID', 'Amount', 'Loan Type', 'Paid']
        check = False

        while check == False:

            path = 'templates/payments/history' +  str(i)  + '.html'
            file = 'payments/history' + str(i) + '.html'
            if os.path.exists(path):
                check = False
                i += 1
            else:
                check = True


        df.to_html(path)
        html = ""
        with open(path, 'r') as myfile:
            html = myfile.read()

        pattern = r"right".format(html)
        html = re.sub(pattern, "left", html)
        with open(path, 'w') as myfile:
            myfile.write('''{% extends "userportal.html" %}
                            {% block details %}
                            ''')
        with open(path, 'a') as myfile:
            myfile.write("<style> tr{color: black;} </style>")
            myfile.write(html)
            myfile.write('{% endblock %}')

        return render_template(file, username = username)

    except Exception as e:
        raise e

    finally:
        con.close()

@app.route('/loans')
def loans():
    #connection
    con = sql.connect(dbpath)
    cur = con.cursor()
    i = 0

    try:
        query = ''' SELECT * FROM LOAN '''

        cur.execute(query)
        rows = cur.fetchall()

        df = pd.DataFrame(rows)
        df.columns = ['Loan ID', 'Amount', 'Interest', 'Tenure', 'Type', 'User ID']
        check = False

        while check == False:

            path = 'templates/credits/loans' +  str(i)  + '.html'
            file = 'credits/loans' + str(i) + '.html'
            if os.path.exists(path):
                check = False
                i += 1
            else:
                check = True


        df.to_html(path)
        html = ""
        with open(path, 'r') as myfile:
            html = myfile.read()

        pattern = r"right".format(html)
        html = re.sub(pattern, "left", html)
        with open(path, 'w') as myfile:
            myfile.write('''{% extends "userportal.html" %}
                            {% block details %}
                            ''')
            myfile.write("<style> tr{color: black;} </style>")
            myfile.write(html)
            myfile.write('{% endblock %}')

        return render_template(file, username = username)

    except Exception as e:
        raise e

    finally:
        con.close()


@app.route('/cindex')
def cindex():

    con = sql.connect('static/Loan Profiles.db')
    cur = con.cursor()
    i=0
    global ccindex
    try:
        query = " SELECT * FROM LOANTYPE "
        cur.execute(query)

        rows = cur.fetchall()
        df = pd.DataFrame(rows)
        df.columns = ['Type', 'Allocation', 'Available', 'Term', 'Months-To-Pay', 'Interest']

        total = (df['Available']**2).sum()

        df['Concentrations'] = df['Available'] ** 2 / total

        ccindex = df['Concentrations'].sum()
        cindex = ccindex
        check = False

        while check == False:

            path = 'templates/cindex/index' +  str(i)  + '.html'
            file = 'cindex/index' + str(i) + '.html'
            if os.path.exists(path):
                check = False
                i += 1
            else:
                check = True

        df.to_html(path)

        html = ""
        with open(path, 'r') as myfile:
            html = myfile.read()

        pattern = r"right".format(html)
        html = re.sub(pattern, "left", html)
        with open(path, 'w') as myfile:
            myfile.write('''{% extends "adminportal.html" %}
                            {% block content %}
                            ''')
        with open(path, 'a') as myfile:
            myfile.write("<style> tr{color: black;} </style>")
            myfile.write(html)
            myfile.write('''<p style="color:red" >Concentration Index : <strong> {{cindex}} </strong></p>''')
            myfile.write('{% endblock %}')

        return render_template(file, cindex = cindex)

    except Exception as e:
        raise e

    finally:
        con.close()

#admin
@app.route('/admin')
@login_required
def admin():
    return render_template('adminportal.html', username=username)


@app.route('/new_application', methods=['GET', 'POST'])
def new():

    con = sql.connect(dbpath)
    cur = con.cursor()
    date_issued = date.today()

    if request.method == 'POST':
        name = request.form.get('name')
        surname =  request.form.get('surname')
        nat_id = request.form.get('nat_id')
        amount = request.form.get('amount')
        interest = request.form.get('interest')
        tenure = request.form.get('tenure')
        sector = request.form.get('sector')

        userid = getID(name, "CREDENTIALS")
        instlmt = instalment(int(interest), int(amount))


        #loan application query
        query = 'INSERT INTO LOAN(AMOUNT, INTEREST, TENURE, LOANTYPE, USERID, DATE_ISSUED) VALUES(?,?,?,?,?,?)'


        cur.execute(query, (amount, interest,tenure, sector, userid, date_issued))
        con.commit()

        query = """UPDATE LOANTYPE
                   SET AVAILABLE = AVAILABLE - ?
                   WHERE TYPE = ?
                   """

        cur.execute(query, (amount, sector))
        con.commit()

    return render_template('issue.html')

@app.route('/first_time_loan_application', methods=['POST', 'GET'])
def application():

    con = sql.connect(dbpath)
    cur = con.cursor()

    if request.method == 'POST':
        name = request.form.get('name')
        surname = request.form.get('surname')
        address = request.form.get('address')
        contact = request.form.get('contact')
        email = request.form.get('email')
        gender = request.form.get('gender')
        nat_id = request.form.get('nat_id')
        salary = request.form.get('salary')
        amount = request.form.get('amount')
        interest = request.form.get('interest')
        tenure = request.form.get('tenure')
        ec = request.form.get('ec')
        sector = request.form.get('sector')
        nok = request.form.get('nok')
        nokAddress = request.form.get('nokAddress')
        nokContact = request.form.get('nokContact')

        query = "INSERT INTO CREDENTIALS(USERNAME, SURNAME, GENDER, NATIONALID, EC, ADDRESS, CONTACT, EMAIL, SALARY, NOK, NOKADDRESS, NOKCONTACT  ) VALUES(?,?,?,?,?,?,?,?,?,?,?, ?)"
        cur.execute(query, (name, surname, gender, nat_id, ec, address, contact, email, salary, nok, nokAddress, nokContact))
        con.commit()

        userid = getID(name, "CREDENTIALS" )
        query = "INSERT INTO LOAN(AMOUNT, INTEREST, TENURE, LOANTYPE, USERID, DATE_ISSUED) VALUES(?,?,?,?,?,?)"
        cur.execute(query, (amount, interest, tenure, sector, userid, date.today()))
        con.commit()

        query = """UPDATE LOANTYPE
                   SET AVAILABLE = ?
                   WHERE TYPE = '?'"""

        cur.execute(query, (amount, sector))
        con.commit()

    return render_template('application.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/logout')
@login_required
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/services')
def services():
    return render_template('services.html')

@app.route('/how-tos')
def how_to_apply():
    return render_template('howtoapply.html')

@app.route('/fees')
def fees():
    return render_template('fees.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/update', methods=['GET', 'POST'])
def update():

    return render_template('update.html')

@app.route('/defaults')
def defaults():

    db = sql.connect(dbpath)
    cur = db.cursor()
    i = 0

    try:
        #query settings
        query = '''SELECT *
                   FROM LOAN
                   WHERE date(DATE_ISSUED) < date('{0}')
                '''.format(date.today() - timedelta(days = 30))

        cur.execute(query)
        rows = cur.fetchall()

        df = pd.DataFrame(rows)
        total = df[1].sum()

        df.columns = ["Loan ID", "Amount", "Interest", "Tenure", "Sector", "Client ID", "Date Issued"]
        df["p(Default) %"] = (df["Amount"] / total) * 100

        probability = df["p(Default) %"].sum() / df.shape[0]

        html = df.to_html()
        pattern = r"right".format(html)
        html = re.sub(pattern, "left", html)

        check = False

        while check == False:

            path = 'templates/defaults/default' +  str(i)  + '.html'
            file = 'defaults/default' + str(i) + '.html'
            if os.path.exists(path):
                check = False
                i += 1
            else:
                check = True

        df.to_html(path)

        with open(path, 'w') as myfile:
            myfile.write('''{% extends "adminportal.html" %}
                            {% block content %}
                            ''')
        with open(path, 'a') as myfile:
            myfile.write("<style> tr{color: black;} </style>")
            myfile.write(html)
            myfile.write('''<p style="color:red" >Probability of Default : <strong> {{probability}} </strong></p>''')
            myfile.write('{% endblock %}')
    except Exception as e:
        raise e

    return render_template(file, probability = probability)



if __name__=="__main__":
    app.run(port=7070, debug=True)
