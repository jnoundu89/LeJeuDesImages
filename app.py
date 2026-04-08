import importlib
import logging
import os
import pkgutil

from dotenv import load_dotenv
from flask import Flask

import models
from models.config import CompanyConfig
from models.employee import EmployeeData
from models.game import GameManager
from models.game_mode import GameMode, GameModeFactory, NormalMode, ReverseMode
from models.score import ScoreManager
from routes.card_game_routes import register_card_game_blueprint
from routes.game_routes import game_bp, init_routes

load_dotenv()
logging.basicConfig(level=logging.INFO)


def create_app():
    app = Flask(__name__)
    app.secret_key = os.environ.get('SECRET_KEY', os.urandom(24))

    # Initialize models
    config = CompanyConfig('config.yaml')
    employee_data = EmployeeData(config)
    score_manager = ScoreManager('scores_db.json')
    game_manager = GameManager(employee_data, score_manager)
    game_mode_factory = GameModeFactory(game_manager)

    # Auto-discover GameMode subclasses
    card_game_mode = None
    for importer, modname, ispkg in pkgutil.iter_modules(models.__path__):
        if modname.endswith('_mode') and modname != 'game_mode':
            module = importlib.import_module(f'models.{modname}')
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (isinstance(attr, type) and issubclass(attr, GameMode)
                        and attr is not GameMode and attr not in (NormalMode, ReverseMode)):
                    instance = attr(game_manager)
                    game_mode_factory.register_mode(instance)
                    # Keep a reference to CardGameMode for its special routes
                    if modname == 'card_game_mode':
                        card_game_mode = instance

    # Initialize routes
    init_routes(game_mode_factory)

    # Register card game routes (needs the specific instance)
    if card_game_mode is not None:
        register_card_game_blueprint(app, card_game_mode)

    # Register blueprints
    app.register_blueprint(game_bp)

    # Inject company branding into all templates
    @app.context_processor
    def inject_company():
        return {
            'company_name': config.company_name,
            'company_logo_url': config.logo_url,
            'company_tagline': config.tagline,
            'company_email': config.contact_email,
        }

    return app

app = create_app()

if __name__ == '__main__':
    app.run(
        host=os.environ.get('FLASK_HOST', '127.0.0.1'),
        port=int(os.environ.get('FLASK_PORT', 5000)),
        debug=os.environ.get('FLASK_DEBUG', 'false').lower() == 'true',
    )
