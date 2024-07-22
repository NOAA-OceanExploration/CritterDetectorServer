from flask import Flask
import os

app = Flask(__name__)

# Load configuration settings
app.config.from_object('config.Config')

# Ensure the upload folder exists
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# Import routes
from app import routes
