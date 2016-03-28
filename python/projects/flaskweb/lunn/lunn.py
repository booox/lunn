#!venv/bin/python
#coding=utf-8

from flask import Flask
from flask import render_template
from flask import url_for
from flask import redirect
from flask import session
from flask import flash
from flask.ext.script import Manager
from flask.ext.script import Shell
from flask.ext.bootstrap import Bootstrap
from flask.ext.moment import Moment
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.migrate import Migrate, MigrateCommand

from flask.ext.wtf import Form
from wtforms import StringField, SubmitField
from wtforms.validators import Required

import os
from datetime import datetime

basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] =\
    'sqlite:///' + os.path.join(basedir, 'data.sqlite')
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True

app.config['SECRET_KEY'] = 'something that hard to guess'

manager = Manager(app)
bootstrap = Bootstrap(app)
moment = Moment(app)

db = SQLAlchemy(app)
migrate = Migrate(app, db)

class NameForm(Form):
    name = StringField('What is your name?', 
                                validators=[Required()])
    submit = SubmitField('Submit')
    
class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    users = db.relationship('User', backref='role', lazy='dynamic')
    
    def __repr__(self):
        return '<Role %r>' % (self.name)
        
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    
    def __repr__(self):
        return '<User %r>' % (self.username)
    
def make_shell_context():
    return dict(app=app, db=db, User=User, Role=Role)
    
    
@app.route('/', methods=['GET', 'POST'])
def index():
    form = NameForm()
    if form.validate_on_submit():
        
        user = User.query.filter_by(username=form.name.data).first()
        if user is None:
            print 'user is None'
            user = User(username = form.name.data)
            db.session.add(user)
            session['known'] = False
        else:
            session['known'] = True
        session['name'] = form.name.data
        form.name.data = ''
        return redirect(url_for('index'))
        
    return render_template('index.html',
                                       name=session.get('name'),
                                       form=form,
                                       known = session.get('known', False),
                                       current_time=datetime.utcnow())
    
@app.route('/user/<name>')
def user(name):
    return render_template('user.html', name=name)
    
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404
    
@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

if __name__ == '__main__':
    # app.run(host='0.0.0.0', debug=True)
    manager.add_command("shell", Shell(make_context=make_shell_context))
    manager.add_command("db", MigrateCommand)
    manager.run()