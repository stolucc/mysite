﻿# -*- coding: utf-8 -*-
import os
from flask import Flask, render_template, flash, redirect, url_for, session, logging, request, Blueprint
from flaskext.mysql import MySQL
from wtforms import Form, SelectField, BooleanField,StringField,IntegerField, TextAreaField, PasswordField, validators, TextField, SubmitField
from passlib.hash import sha256_crypt
from functools import wraps
from pymysql.cursors import DictCursor
#from flask_sslify import SSLify
from utilities import *
from werkzeug.utils import secure_filename
from forms import *
from Registration import *
from Proposal import *
from Dashboard import *
from Profile import *

UPLOAD_FOLDER = 'storage/proposals'

app = Flask(__name__)
#sslify = SSLify(app)
app.secret_key = 'alphaHodder'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

app.register_blueprint(dashboard_page)
app.register_blueprint(registration_page)
app.register_blueprint(proposal_page)
app.register_blueprint(profile_page)

# Initialise MySQL
mysql = MySQL(cursorclass=DictCursor)
mysql.init_app(app)

# Check for user auth
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('You must be logged in to view this page', 'danger')
            return redirect(url_for('login'))
    return wrap

@app.route('/')
def index():
    try:
        connection = create_connection()
        with connection.cursor() as cursor:
            #get data from tables
            cursor.execute('SELECT * FROM CFP')
            cfp_data = cursor.fetchall()
    finally:
        connection.close()
    return render_template('index.html',cfp_data=cfp_data)

# Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password_candidate = request.form['password']
        cursor = create_connection().cursor()
        result = cursor.execute('SELECT * FROM Users WHERE email = %s', [email])
        form = RegistrationType(request.form)
        
        if result > 0:
            data = cursor.fetchone()
            password = data['password']
            user_type = data['user_type']
            # Compare Passwords
            if sha256_crypt.verify(password_candidate, password):
                # Passed
                session['logged_in'] = True
                session['email'] = email
                #Admin or not
                if user_type == "A":
                    flash('logged in as admin', 'success')
                    return redirect(url_for('dashboard_page.adminDashboard'))
                elif user_type == "C":
                    flash('logged in as consultant', 'success')
                    return redirect(url_for('dashboard_page.reviewerDashboard'))
                elif user_type == "U":
                    flash('logged in as university admin', 'success')
                    return redirect(url_for('dashboard_page.universityDashboard'))
                else:
                    flash('logged in as researcher', 'success')
                    return redirect(url_for('dashboard_page.dashboard'))
            else:
                error = 'Invalid login'
                return render_template('login.html', error=error)
            cursor.close()
        else:
            error = 'Username not found'
            return render_template('login.html', error=error)

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You are now logged out', 'success')
    return redirect(url_for('login'))

@app.route('/profile', methods=['GET', 'POST'])
@is_logged_in
def show_profile():
    form1 = BasicProfileForm(request.form)
    form2 = ProfileEducationForm(request.form)
    form3 = ProfileEmploymentForm(request.form)
    form4 = ProfileProfessSocForm(request.form)
    form5 = ProfileDandAForm(request.form)
    form6 = ProfileFundingForm(request.form)
    form7 = ProfileTeamateForm(request.form)
    form8 = ProfileImpactForm(request.form)
    form9 = passwordSet(request.form)
    if 'email' in session:
        email = session['email']
    if request.method == 'POST':
        connection = create_connection()
        with connection.cursor() as cursor:
            if request.form['submit'] == 'Save Personal Info' and form1.validate():
                cursor.execute('UPDATE Users SET first_name=%s, surname=%s, suffix=%s, job_title=%s, institution=%s,'
                               'orcid=%s, phone=%s, phone_extension=%s'
                               'WHERE email=%s',
                               [form1.first_name.data, form1.surname.data, form1.suffix.data, form1.job_title.data,
                                form1.institution.data, form1.orcid.data, form1.phone.data, form1.phone_extension.data,
                                email])
                connection.commit()

            elif request.form['submit'] == 'Add Education Info' and form2.validate():
                cursor.execute('INSERT INTO Profile_Education_Info (email, degree, field_of_study, institution, location, degree_year)'
                               ' VALUES (%s, %s, %s, %s, %s, %s)',
                               [email, form2.degree.data, form2.field_of_study.data, form2.institution.data, form2.location.data, form2.degree_year.data])
                connection.commit()
                pass
            elif request.form['submit'] == 'Remove Education Info':
                cursor.execute('DELETE FROM Profile_Education_Info WHERE degree=%s AND email=%s', [request.form['degree'], email])
                connection.commit()

            elif request.form['submit'] == 'Add Employment Info' and form3.validate():
                cursor.execute(
                    'INSERT INTO Profile_Employment (email, institution, location, start_date, end_date)'
                    ' VALUES (%s, %s, %s, %s, %s)',
                    [email, form3.institution.data, form3.location.data, form3.start_date.data, form3.end_date.data])
                connection.commit()
            elif request.form['submit'] == 'Remove Employment Info':
                cursor.execute('DELETE FROM Profile_Employment WHERE institution=%s AND email=%s',
                               [request.form['institution'], email])
                connection.commit()


            elif request.form['submit'] == 'Add Society Info' and form4.validate():
                cursor.execute('INSERT INTO Profile_Profess_soc (email, start_date,end_date,name_of_soc,type_of_membership,status)'
                               ' VALUES (%s, %s, %s, %s, %s, %s)',
                               [email, form4.start_date.data, form4.end_date.data, form4.name_of_soc.data, form4.type_of_membership.data, form4.status.data])
                connection.commit()
                pass
            elif request.form['submit'] == 'Remove Society Info':
                cursor.execute('DELETE FROM Profile_Profess_soc WHERE name_of_soc=%s AND email=%s',
                               [request.form['society'], email])
                connection.commit()

            elif request.form['submit'] == 'Add Award Info' and form5.validate():
                cursor.execute('INSERT INTO Profile_DandA (email, DandA_year,award_body,detail,teamate_name)'
                               ' VALUES (%s, %s, %s, %s, %s)',
                               [email, form5.DandA_year.data, form5.award_body.data, form5.detail.data, form5.teamate_name.data])
                connection.commit()
                pass
            elif request.form['submit'] == 'Remove Award Info':
                cursor.execute('DELETE FROM Profile_DandA WHERE award_body=%s AND email=%s',
                               [request.form['body'], email])
                connection.commit()
            elif request.form['submit'] == 'Add Funding Info' and form6.validate():
                cursor.execute('INSERT INTO Profile_Funding (email, start_date,end_date,amount_fund,fund_body,fund_program,status,grant_no)'
                               ' VALUES (%s, %s, %s, %s, %s, %s, %s, %s)',
                               [email, form6.start_date.data, form6.end_date.data, form6.amount_fund.data, form6.fund_body.data, form6.fund_program.data, form6.status.data, form6.grant_no.data])
                connection.commit()
                pass
            elif request.form['submit'] == 'Remove Funding Info':
                cursor.execute('DELETE FROM Profile_Funding WHERE grant_no=%s AND email=%s',
                               [request.form['grant'], email])
                connection.commit()

            elif request.form['submit'] == 'Add Team Member Info' and form7.validate():
                cursor.execute('INSERT INTO Profile_Teamate (email, start_date,depart_date,name,position,grant_no)'
                               ' VALUES ( %s, %s, %s, %s, %s, %s)',
                               [email, form7.start_date.data, form7.depart_date.data, form7.name.data, form7.position.data, form6.grant_no.data])
                connection.commit()
                pass
            elif request.form['submit'] == 'Remove Team Member Info':
                cursor.execute('DELETE FROM Profile_Teamate WHERE name=%s AND email=%s',
                               [request.form['name'], email])
                connection.commit()

            elif request.form['submit'] == 'Add Impact Info' and form8.validate():
                cursor.execute('INSERT INTO Profile_Impact (email, impact_title,impact_category,primary_beneficiary,grant_no)'
                               ' VALUES ( %s, %s, %s, %s, %s)',
                               [email, form8.impact_title.data, form8.impact_category.data, form8.primary_beneficiary.data, form8.grant_no.data])
                connection.commit()
                pass
            elif request.form['submit'] == 'Remove Impact Info':
                cursor.execute('DELETE FROM Profile_Impact WHERE grant_no=%s AND email=%s',
                               [request.form['grant'], email])
                connection.commit()
            elif request.form['submit'] == 'Change Password':
                if form9.validate():
                    passw = sha256_crypt.encrypt(str(form9.password.data))
                    cursor.execute('UPDATE Users SET password=%s WHERE email=%s', [passw, email])
                    connection.commit()

                else:
                    flash('Passwords do not match')



    try:
        connection = create_connection()
        with connection.cursor() as cursor:

            #redirect to basic show profile page if not verified
            cursor.execute('SELECT is_verified FROM Users WHERE email = %s', [email])
            verified = cursor.fetchone()

            #get data from tables
            cursor.execute('SELECT * FROM Users WHERE email = %s', [email])
            p1_data = cursor.fetchone()

            cursor.execute('SELECT * FROM Profile_Education_Info WHERE email = %s', [email])
            p2_data = cursor.fetchall()

            cursor.execute('SELECT * FROM Profile_Employment WHERE email = %s', [email])
            p3_data = cursor.fetchall()

            cursor.execute('SELECT * FROM Profile_Profess_soc WHERE email = %s', [email])
            p4_data = cursor.fetchall()

            cursor.execute('SELECT * FROM Profile_DandA WHERE email = %s', [email])
            p5_data = cursor.fetchall()

            cursor.execute('SELECT * FROM Profile_Funding WHERE email = %s', [email])
            p6_data = cursor.fetchall()

            cursor.execute('SELECT * FROM Profile_Teamate WHERE email = %s', [email])
            p7_data = cursor.fetchall()

            cursor.execute('SELECT * FROM Profile_Impact WHERE email = %s', [email])
            p8_data = cursor.fetchall()

            cursor.execute('SELECT * FROM Profile_IandC WHERE email = %s', [email])
            p9_data = cursor.fetchall()

            cursor.execute('SELECT * FROM Profile_Publications WHERE email = %s', [email])
            p10_data = cursor.fetchall()

            cursor.execute('SELECT * FROM Profile_Presentation WHERE email = %s', [email])
            p11_data = cursor.fetchall()

            cursor.execute('SELECT * FROM Profile_Academic_Col WHERE email = %s', [email])
            p12_data = cursor.fetchall()

            cursor.execute('SELECT * FROM Profile_None_Academic_Col WHERE email = %s', [email])
            p13_data = cursor.fetchall()

            cursor.execute('SELECT * FROM Profile_Workshop WHERE email = %s', [email])
            p14_data = cursor.fetchall()

            cursor.execute('SELECT * FROM Profile_Communication WHERE email = %s', [email])
            p15_data = cursor.fetchall()

            cursor.execute('SELECT * FROM Profile_SFI_Fund_Ratio WHERE email = %s', [email])
            p16_data = cursor.fetchall()

            cursor.execute('SELECT * FROM Profile_Public_Engagement WHERE email = %s', [email])
            p17_data = cursor.fetchall()
    finally:
        connection.close()

    if verified == {u'is_verified': 0}:
        return render_template('basicShowProfile.html' , form1=form1, form2=form2, form3=form3, p1_data=p1_data, p2_data=p2_data, p3_data=p3_data, p4_data=p4_data, p5_data=p5_data, p6_data=p6_data, p7_data=p7_data, p8_data=p8_data, p9_data=p9_data, p10_data=p10_data, p11_data=p11_data, p13_data=p13_data, p14_data=p14_data, p16_data=p16_data, p17_data=p17_data)
    return render_template('new_show_profile.html', form1=form1, form2=form2, form3=form3,form4=form4,form5=form5,form6=form6,form7=form7,form8=form8, form9=form9, p1_data=p1_data, p2_data=p2_data, p3_data=p3_data, p4_data=p4_data, p5_data=p5_data, p6_data=p6_data, p7_data=p7_data, p8_data=p8_data, p9_data=p9_data, p10_data=p10_data, p11_data=p11_data, p13_data=p13_data, p14_data=p14_data, p16_data=p16_data, p17_data=p17_data)


@app.route('/activeProjects')
@is_logged_in
def activeProjects():
    if 'email' in session:
        email = session['email']
    try:
        connection = create_connection()
        with connection.cursor() as cursor:
            cursor.execute('SELECT * FROM Project WHERE email = %s AND active = %s', [email, 'y'])
            rows = cursor.fetchall()

    finally:
       connection.close()
    return render_template('activeProjects.html', rows=rows)

@app.route('/adminProjects')
@is_logged_in
def adminProjects():
    if 'email' in session:
        email = session['email']
    try:
        connection = create_connection()
        with connection.cursor() as cursor:
            cursor.execute('SELECT * FROM Project WHERE active = %s', ['y'])
            rows = cursor.fetchall()

    finally:
       connection.close()
    return render_template('adminProjects.html', rows=rows)

@app.route('/yearlyReports', methods=['GET', 'POST'])
@is_logged_in
def yearlyReports():
    YRform = yearlyReportForm(request.form)
    if 'email' in session:
        email = session['email']
    if request.method == 'POST':
        connection = create_connection()
        with connection.cursor() as cursor:
            if request.form['submit'] == 'Submmit records' and YRform.validate():
                cursor.execute('UPDATE Users SET publications=%s, eduPub=%s, academic_collaborations=%s, '
                               'non_academic_collaborations=%s, commercialisation=%s, '
                               'deviations_of_research=%s, bullet_research_point=%s, challenges=%s, impact=%s, '
                               'plannes_activities=%s '
                               'WHERE email=%s',
                               [YRform.publications.data,YRform.eduPub.data,YRform.academic_collaborations.data,YRform.non_academic_collaborations.data,YRform.commercialisation.data,YRform.deviations_of_research.data,YRform.bullet_research_point.data,YRform.challenges.data,YRform.impact.data,YRform.planned_activities.data,
                                email])
                connection.commit()

    try:
        connection = create_connection()
        with connection.cursor() as cursor:

            # redirect to basic show profile page if not verified
            cursor.execute('SELECT is_verified FROM Users WHERE email = %s', [email])
            verified = cursor.fetchone()

            # get data from tables
            cursor.execute('SELECT * FROM Users WHERE email = %s', [email])
            p1_data = cursor.fetchone()

            cursor.execute('SELECT * FROM Profile_Education_Info WHERE email = %s', [email])
            p2_data = cursor.fetchall()

            cursor.execute('SELECT * FROM Profile_Employment WHERE email = %s', [email])
            p3_data = cursor.fetchall()

            cursor.execute('SELECT * FROM Profile_Profess_soc WHERE email = %s', [email])
            p4_data = cursor.fetchall()

            cursor.execute('SELECT * FROM Profile_DandA WHERE email = %s', [email])
            p5_data = cursor.fetchall()

            cursor.execute('SELECT * FROM Profile_Funding WHERE email = %s', [email])
            p6_data = cursor.fetchall()

            cursor.execute('SELECT * FROM Profile_Teamate WHERE email = %s', [email])
            p7_data = cursor.fetchall()

            cursor.execute('SELECT * FROM Profile_Impact WHERE email = %s', [email])
            p8_data = cursor.fetchall()

            cursor.execute('SELECT * FROM Profile_IandC WHERE email = %s', [email])
            p9_data = cursor.fetchall()

            cursor.execute('SELECT * FROM Profile_Publications WHERE email = %s', [email])
            p10_data = cursor.fetchall()


    finally:
        connection.close()

    if verified == {u'is_verified': 0}:
        return render_template('basicShowProfile.html', YRform=YRform, p1_data=p1_data,
                               p2_data=p2_data, p3_data=p3_data, p4_data=p4_data, p5_data=p5_data, p6_data=p6_data,
                               p7_data=p7_data, p8_data=p8_data, p9_data=p9_data, p10_data=p10_data)
    return render_template('yearlyReports.html', YRform=YRform, p1_data=p1_data,
                           p2_data=p2_data, p3_data=p3_data, p4_data=p4_data, p5_data=p5_data, p6_data=p6_data,
                           p7_data=p7_data, p8_data=p8_data, p9_data=p9_data, p10_data=p10_data)

@app.route('/fundingstatus')
@is_logged_in
def fundingstatus():
    if 'email' in session:
        email = session['email']
    try:
        connection = create_connection()
        with connection.cursor() as cursor:
            cursor.execute('SELECT * FROM Profile_Funding WHERE email = %s', [email])
            fdata = cursor.fetchall()

    finally:
        connection.close()
    return render_template('fundingStatus.html', fdata=fdata)

if __name__ == '__main__':
    #app.run(ssl_context='adhoc')
    mail_check()
    app.run(debug=True)
