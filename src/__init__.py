import os
import sys

from flask import Flask, jsonify, redirect

from src.auth import auth
from src.config.swagger import template, swagger_config
from src.bookmarks import bookmarks
from src.constants.http_status_codes import HTTP_404_NOT_FOUND, HTTP_500_INTERNAL_SERVER_ERROR
from src.database import Bookmark, db
from flask_jwt_extended import JWTManager
from flasgger import Swagger, swag_from


def create_app(test_config=None):
    app = Flask(__name__,instance_relative_config=True)

    if test_config is None:
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///bookmarks.db'
        app.config['SECRET_KEY'] = 'dev'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        app.config['JWT_SECRET_KEY'] = 'JWT_SECRET_KEY'
        app.config['SWAGGER'] = {
            'title':"Bookmark Api",
            'uiversion':3
        }
      
    else:
        app.config.from_mapping(test_config)

    db.app=app
    db.init_app(app)

    JWTManager(app)

    app.register_blueprint(auth)
    app.register_blueprint(bookmarks)
    
    Swagger(app, config=swagger_config, template=template)
    
    @app.get('/<short_url>')
    @swag_from('./doc/short_url.yml')
    def redirect_to_url(short_url):
        bookmark = Bookmark.query.filter_by(short_url=short_url).first_or_404()
        
        if bookmark:
            bookmark.visits=bookmark.visits + 1
            db.session.commit()
            
            return redirect(bookmark.url)
        
    @app.errorhandler(HTTP_404_NOT_FOUND)
    def handle_404(e):
        return jsonify({'error':'not found'}),HTTP_404_NOT_FOUND
    
    @app.errorhandler(HTTP_500_INTERNAL_SERVER_ERROR)
    def handle_500(e):
        return jsonify({'error':'something went wrong'}),HTTP_500_INTERNAL_SERVER_ERROR
    
    return app 