from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from os import path
from flask_login import LoginManager



db = SQLAlchemy()
DB_NAME = "database.db"

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] ='devendrajha'
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_NAME}'
    db.init_app(app)
    
    from .store import store
    app.register_blueprint(store, url_prefix="/")
    from .api import api
    app.register_blueprint(api, url_prefix="/")
    
    
    from .database import User, Categories, Products, Booking

    with app.app_context():
        db.create_all()

    login_manager = LoginManager()
    login_manager.login_view = "store.login"
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(id):
        return User.query.get(int(id))

    return app




def create_database(app):
    if not path.exists("Application/" + DB_NAME):
        db.create_all(app=app)
        print("Created database!")
