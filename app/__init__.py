from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bcrypt import Bcrypt

# Initialize the app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'kjzhnrsgipuhs3489790yhg4793'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:postgres@localhost/flaskSite2'

# Initialize extensions
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

# Import the routes
from app import routes

# Create all the database tables
with app.app_context():
    db.create_all()
