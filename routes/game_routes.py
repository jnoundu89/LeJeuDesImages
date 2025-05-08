# routes/game_routes.py
from flask import Blueprint, render_template, request, redirect, url_for, session
import logging
from models.game_mode import GameModeFactory

# Create a Blueprint for game routes
game_bp = Blueprint('game', __name__)

def init_routes(game_mode_factory: GameModeFactory):
    """
    Initialize the game routes with the provided game mode factory.

    Args:
        game_mode_factory: GameModeFactory instance for accessing game modes
    """

    @game_bp.route('/')
    def index():
        """
        Render the mode selection page.
        """
        # Get all available game modes for display
        modes = game_mode_factory.get_all_modes()
        mode_info = [{'name': mode.name, 'description': mode.description} for mode in modes.values()]

        return render_template('mode_selection.html', modes=mode_info)

    @game_bp.route('/mode_selection')
    def mode_selection():
        """
        Render the mode selection page.
        """
        return index()

    @game_bp.route('/mode/<mode_name>')
    def start_mode(mode_name):
        """
        Start a game mode.

        Args:
            mode_name: Name of the game mode to start
        """
        logging.info(f"Mode {mode_name} selected")

        # Get the game mode
        mode = game_mode_factory.get_mode(mode_name)
        if mode is None:
            logging.error(f"Game mode {mode_name} not found")
            return redirect(url_for('game.index'))

        # Initialize the game mode
        user_id = session.get('user_id')
        game_data = mode.initialize(user_id)

        # Store game data in session
        session['user_id'] = game_data['user_id']
        session['data_id'] = game_data['data_id']
        session['reverse_mode'] = game_data.get('reverse_mode', False)
        session['max_score'] = game_data.get('max_score', 0)
        session['all_indices'] = []
        session['used_indices'] = []
        session['current_question'] = 0
        session['mode_name'] = mode_name  # Store the original mode name

        return redirect(url_for('game.question'))

    @game_bp.route('/question')
    def question():
        """
        Render the question page.
        """
        # Check if game is initialized
        if 'data_id' not in session:
            logging.error("Game not initialized")
            return redirect(url_for('game.index'))

        # Get the game mode
        mode_name = session.get('mode_name')
        if not mode_name:
            # Fallback to reverse/normal for backward compatibility
            mode_name = "reverse" if session.get('reverse_mode', False) else "normal"
        mode = game_mode_factory.get_mode(mode_name)
        if mode is None:
            logging.error(f"Game mode {mode_name} not found")
            return redirect(url_for('game.index'))

        # Initialize session variables if needed
        if 'all_indices' not in session:
            session['all_indices'] = []
        if 'used_indices' not in session:
            session['used_indices'] = []
        if 'current_question' not in session:
            session['current_question'] = 0

        # Get question data
        question_data = mode.get_question_data(
            session['data_id'], 
            session['used_indices'], 
            session['current_question']
        )

        # Check if game is over
        if question_data.get('game_over', False):
            return redirect(url_for('game.result'))

        # Update session
        session['current_question'] = question_data.get('current_question', session['current_question'])
        session.modified = True

        # Get user stats
        user_id = session.get('user_id')
        user_score = mode.game_manager.score_manager.get_user_score(user_id)
        stats = mode.game_manager.score_manager.get_stats(user_id)

        # Prepare template data
        template_data = {
            'maxScore': session.get('max_score', 0),
            'stats': stats,
            'currentScore': user_score['score'],
            'total_questions': len(session['used_indices']),
            'current_question': session.get('current_question', 0),
            'total_employees': len(mode.game_manager.get_game_data(session['data_id']))
        }

        # Add question-specific data
        if mode_name == "normal":
            template_data.update({
                'image_url': question_data['image_url'],
                'company': question_data['correct_values']['company'],
                'team': question_data['correct_values']['team'],
                'name': question_data['correct_values']['name'],
                'position': question_data['correct_values']['position'],
                'companies': question_data['choices']['companies'],
                'teams': question_data['choices']['teams'],
                'names': question_data['choices']['names'],
                'positions': question_data['choices']['positions']
            })
        elif mode_name == "reverse":
            template_data.update({
                'correct_value': question_data['correct_value'],
                'choices': question_data['choices']
            })
        elif mode_name == "pixelation":
            template_data.update({
                'image_url': question_data['image_url'],
                'correct_name': question_data['correct_name'],
                'name_choices': question_data['name_choices']
            })
        else:  # Handle any other modes generically
            # Just pass all question data to the template
            template_data.update(question_data)

        return render_template(mode.template, **template_data)

    @game_bp.route('/check', methods=['POST'])
    def check():
        """
        Check the answer and update the score.
        """
        # Check if game is initialized
        if 'data_id' not in session:
            logging.error("Game not initialized")
            return redirect(url_for('game.index'))

        # Get the game mode
        mode_name = session.get('mode_name')
        if not mode_name:
            # Fallback to reverse/normal for backward compatibility
            mode_name = "reverse" if session.get('reverse_mode', False) else "normal"
        mode = game_mode_factory.get_mode(mode_name)
        if mode is None:
            logging.error(f"Game mode {mode_name} not found")
            return redirect(url_for('game.index'))

        # Get user ID
        user_id = session.get('user_id')

        # Update score based on game mode
        if mode_name == "normal":
            score_increment = int(request.form.get('score_increment', 0))
            company_correct = int(request.form.get('company_correct', 0))
            team_correct = int(request.form.get('team_correct', 0))
            name_correct = int(request.form.get('name_correct', 0))
            position_correct = int(request.form.get('position_correct', 0))

            mode.update_score(
                user_id, 
                score_increment=score_increment,
                company_correct=company_correct,
                team_correct=team_correct,
                name_correct=name_correct,
                position_correct=position_correct
            )
        else:  # reverse mode or other modes (like pixelation)
            correct_answer = int(request.form.get('correct_answer', 0))
            mode.update_score(user_id, correct_answer=correct_answer)

        return redirect(url_for('game.question'))

    @game_bp.route('/result')
    def result():
        """
        Render the result page.
        """
        # Check if game is initialized
        if 'data_id' not in session:
            logging.error("Game not initialized")
            return redirect(url_for('game.index'))

        # Get the game mode
        mode_name = session.get('mode_name')
        if not mode_name:
            # Fallback to reverse/normal for backward compatibility
            mode_name = "reverse" if session.get('reverse_mode', False) else "normal"
        mode = game_mode_factory.get_mode(mode_name)
        if mode is None:
            logging.error(f"Game mode {mode_name} not found")
            return redirect(url_for('game.index'))

        # Get result data
        user_id = session.get('user_id')
        max_score = session.get('max_score', 0)
        total_questions = len(session.get('used_indices', []))

        result_data = mode.game_manager.get_result_data(user_id, max_score, total_questions)

        return render_template('result.html', **result_data)

    @game_bp.route('/restart')
    def restart():
        """
        Restart the game.
        """
        session.clear()
        return redirect(url_for('game.index'))

    @game_bp.route('/arr')
    def arr_easter_egg():
        """
        Easter egg route for the ARR game mode.
        """
        return render_template('arr.html')
