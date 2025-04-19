from flask import Flask
import logging
from models.employee import EmployeeData
from models.score import ScoreManager
from models.game import GameManager
from models.game_mode import GameModeFactory
from models.example_mode import ExampleMode
from routes.game_routes import game_bp, init_routes

# Configuration du logging
logging.basicConfig(level=logging.INFO)

def create_app():
    """
    Create and configure the Flask application.

    Returns:
        Flask application instance
    """
    app = Flask(__name__)
    app.secret_key = 'secret123'

    # Initialize models
    employee_data = EmployeeData("infolegale_team.csv")
    score_manager = ScoreManager('scores_db.json')
    game_manager = GameManager(employee_data, score_manager)
    game_mode_factory = GameModeFactory(game_manager)

    # Register the example game mode
    game_mode_factory.register_mode(ExampleMode(game_manager))

    # Initialize routes
    init_routes(game_mode_factory)

    # Register blueprints
    app.register_blueprint(game_bp)

    return app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
