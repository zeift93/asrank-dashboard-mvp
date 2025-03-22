from flask import Flask
from app.models import db
from app.routes.as_data import as_data_bp
from app.routes.etl import etl_bp
from app.routes.export import export_bp
from app.routes.rank import rank_bp
from app.routes.competitor import competitor_bp
from app.routes.alerts import alerts_bp

def create_app():
    app = Flask(__name__, instance_relative_config=False)
    app.config.from_pyfile('app/config.py')

    db.init_app(app)

    # Register blueprints
    app.register_blueprint(as_data_bp, url_prefix='/api/as')
    app.register_blueprint(etl_bp, url_prefix='/api/etl')
    app.register_blueprint(export_bp, url_prefix='/export')
    app.register_blueprint(rank_bp, url_prefix='/api/as')
    app.register_blueprint(competitor_bp, url_prefix='/api/competitor')
    app.register_blueprint(alerts_bp, url_prefix='/api/alerts')

    return app

if __name__ == '__main__':
    create_app().run(debug=True)
