from flask import Blueprint

base = Blueprint('views', __name__)

from . import routes

