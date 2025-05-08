from flask import Flask
import logging
from models.employee import EmployeeData
from models.score import ScoreManager
from models.game import GameManager
from models.game_mode import GameModeFactory
from models.pixelation_mode import PixelationMode
from models.timed_mode import TimedMode
from models.team_mode import TeamMode
from models.clue_mode import ClueMode
from models.memory_mode import MemoryMode
from models.quiz_mode import QuizMode
from models.arr_mode import ARRMode
from models.speed_mode import SpeedMode
from models.team_guess_mode import TeamGuessMode
from models.missing_person_mode import MissingPersonMode
from models.position_match_mode import PositionMatchMode
from models.progressive_hint_mode import ProgressiveHintMode
from models.scrambled_face_mode import ScrambledFaceMode
from models.emoji_challenge_mode import EmojiChallengeMode
from models.silhouette_mode import SilhouetteMode
from models.mirror_mode import MirrorMode
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

    # Register all game modes
    game_mode_factory.register_mode(PixelationMode(game_manager))
    game_mode_factory.register_mode(TimedMode(game_manager))
    game_mode_factory.register_mode(TeamMode(game_manager))
    game_mode_factory.register_mode(ClueMode(game_manager))
    game_mode_factory.register_mode(MemoryMode(game_manager))
    game_mode_factory.register_mode(QuizMode(game_manager))
    game_mode_factory.register_mode(ARRMode(game_manager))

    # Register new game modes
    game_mode_factory.register_mode(SpeedMode(game_manager))
    game_mode_factory.register_mode(TeamGuessMode(game_manager))
    game_mode_factory.register_mode(MissingPersonMode(game_manager))
    game_mode_factory.register_mode(PositionMatchMode(game_manager))
    game_mode_factory.register_mode(ProgressiveHintMode(game_manager))

    # Register fun and crazy game modes
    game_mode_factory.register_mode(ScrambledFaceMode(game_manager))
    game_mode_factory.register_mode(EmojiChallengeMode(game_manager))
    game_mode_factory.register_mode(SilhouetteMode(game_manager))
    game_mode_factory.register_mode(MirrorMode(game_manager))

    # Initialize routes
    init_routes(game_mode_factory)

    # Register blueprints
    app.register_blueprint(game_bp)

    return app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
