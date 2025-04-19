import random
import pandas as pd
from flask import Flask, render_template, request, redirect, url_for, session
from tinydb import TinyDB, Query
import logging

app = Flask(__name__)
app.secret_key = 'secret123'

# Configuration du logging
logging.basicConfig(level=logging.INFO)

# Configuration de TinyDB
db = TinyDB('scores_db.json')
scores_table = db.table('user_scores')

data = pd.read_csv("infolegale_team.csv")


@app.route('/')
def index():
    return render_template('mode_selection.html')


@app.route('/mode_selection')
def mode_selection():
    return render_template('mode_selection.html')


@app.route('/normal')
def normal():
    logging.info("Mode normal sélectionné")
    session['reverse_mode'] = False
    initialize_user()
    session['data_id'] = store_data_in_db(data.to_dict('records'))
    return redirect(url_for('question'))


@app.route('/reverse')
def reverse():
    logging.info("Mode reverse sélectionné")
    session['reverse_mode'] = True
    initialize_user()
    session['data_id'] = store_data_in_db(
        data.sample(frac=1).to_dict('records'))  # Mélanger les données pour le mode reverse
    return redirect(url_for('question'))


@app.route('/question')
def question():
    if 'reverse_mode' not in session:
        return redirect(url_for('index'))

    if 'all_indices' not in session:
        session['all_indices'] = list(range(len(get_data_from_db(session['data_id']))))
        random.shuffle(session['all_indices'])
    if 'used_indices' not in session:
        session['used_indices'] = []
    if 'maxScore' not in session:
        session['maxScore'] = len(get_data_from_db(session['data_id'])) * 4  # Nombre total de questions * 4
    if 'current_question' not in session:
        session['current_question'] = 0

    if len(session['used_indices']) >= len(get_data_from_db(session['data_id'])):
        return redirect(url_for('result'))

    available_indices = [i for i in session['all_indices'] if i not in session['used_indices']]
    if not available_indices:
        return redirect(url_for('result'))

    index = available_indices[0]
    session['used_indices'].append(index)
    session['current_question'] += 1
    session.modified = True

    selected_row = get_data_from_db(session['data_id'])[index]
    correct_values = {
        'company': selected_row['company'],
        'team': selected_row['team'],
        'name': selected_row['name'],
        'position': selected_row['position']
    }

    user_id = session.get('user_id')
    User = Query()
    user_score = scores_table.get(User.user_id == user_id)
    stats = {
        'company': user_score['stats_company'],
        'team': user_score['stats_team'],
        'name': user_score['stats_name'],
        'position': user_score['stats_position']
    }
    currentScore = user_score['score']
    total_questions = len(session['used_indices'])

    data_df = pd.DataFrame(get_data_from_db(session['data_id']))

    if session['reverse_mode']:
        # Mode reverse avec filtrage par sexe
        sex_filter = selected_row['sex']
        filtered_data = data_df[data_df['sex'] == sex_filter]

        # Sélectionner 3 personnes aléatoires du même sexe (en plus de la personne correcte)
        other_choices = filtered_data[filtered_data['name'] != selected_row['name']].sample(3)

        # Combiner avec la personne correcte
        choices_df = pd.concat([pd.DataFrame([selected_row]), other_choices])
        choices_df = choices_df.sample(frac=1).reset_index(drop=True)  # Mélanger

        return render_template('reverse.html',
                              correct_value=correct_values['name'],
                              choices=choices_df,
                              maxScore=session['maxScore'],
                              stats=stats,
                              currentScore=currentScore,
                              total_questions=total_questions)
    else:
        # Mode normal - logique basée sur l'ancien code
        # Filtrer les données par sexe pour les noms et postes
        sex_filter = selected_row['sex']
        filtered_data = data_df[data_df['sex'] == sex_filter]

        # Fonction pour obtenir des choix aléatoires
        def get_random_choices(column, filter_data):
            unique_values = list(filter_data[column].unique())
            if correct_values[column] not in unique_values:
                unique_values.append(correct_values[column])
            choices = random.sample(unique_values, min(4, len(unique_values)))
            if correct_values[column] not in choices:
                choices[random.randint(0, min(3, len(choices) - 1))] = correct_values[column]
            random.shuffle(choices)  # Mélanger les choix
            return choices

        # Générer les choix selon la logique de l'ancien code
        companies = ['Infolegale', 'Eloficash']  # Options fixes
        teams = get_random_choices('team', data_df)
        names = get_random_choices('name', filtered_data)
        positions = get_random_choices('position', filtered_data)

        return render_template('index.html',
                              image_url=selected_row['image_url'],
                              company=correct_values['company'],
                              team=correct_values['team'],
                              name=correct_values['name'],
                              position=correct_values['position'],
                              companies=companies,
                              teams=teams,
                              names=names,
                              positions=positions,
                              maxScore=session['maxScore'],
                              stats=stats,
                              currentScore=currentScore,
                              total_questions=total_questions)

@app.route('/check', methods=['POST'])
def check():
    if 'reverse_mode' not in session:
        return redirect(url_for('index'))

    user_id = session.get('user_id')
    User = Query()
    user_score = scores_table.get(User.user_id == user_id)

    if session['reverse_mode']:
        correct_value = request.form['correct_value']
        correct_answer = int(request.form['correct_answer'])
        if correct_answer:
            user_score['score'] += 1
            user_score['total_correct_answers'] += 1
        scores_table.update(user_score, User.user_id == user_id)
        return redirect(url_for('question'))
    else:
        score_increment = int(request.form.get('score_increment', 0))

        # Récupération des réponses correctes par catégorie
        company_correct = int(request.form.get('company_correct', 0))
        team_correct = int(request.form.get('team_correct', 0))
        name_correct = int(request.form.get('name_correct', 0))
        position_correct = int(request.form.get('position_correct', 0))

        # Mise à jour du score et des statistiques
        user_score['score'] += score_increment
        user_score['total_correct_answers'] += score_increment

        if company_correct:
            user_score['stats_company'] += 1
        if team_correct:
            user_score['stats_team'] += 1
        if name_correct:
            user_score['stats_name'] += 1
        if position_correct:
            user_score['stats_position'] += 1

        scores_table.update(user_score, User.user_id == user_id)
        logging.info(f"Score mis à jour pour l'utilisateur {user_id}: {user_score['score']}")

        return redirect(url_for('question'))


@app.route('/result')
def result():
    user_id = session.get('user_id')
    User = Query()
    user_score = scores_table.get(User.user_id == user_id)

    stats = {
        'company': user_score.get('stats_company', 0),
        'team': user_score.get('stats_team', 0),
        'name': user_score.get('stats_name', 0),
        'position': user_score.get('stats_position', 0)
    }

    currentScore = user_score['score']
    total_questions = len(session['used_indices']) if 'used_indices' in session else 0

    return render_template('result.html',
                           score=user_score['score'],
                           maxScore=session.get('maxScore', 0),
                           currentScore=currentScore,
                           total_questions=total_questions,
                           stats=stats)


@app.route('/restart')
def restart():
    session.clear()
    return redirect(url_for('index'))


def initialize_user():
    if 'user_id' not in session:
        session['user_id'] = random.randint(1000, 9999)
        scores_table.insert({
            'user_id': session['user_id'],
            'score': 0,
            'stats_company': 0,
            'stats_team': 0,
            'stats_name': 0,
            'stats_position': 0,
            'total_correct_answers': 0
        })
        logging.info(f"Nouvel utilisateur créé: {session['user_id']}")

    User = Query()
    user_id = session.get('user_id')
    user_score = scores_table.get(User.user_id == user_id)

    if user_score is None:
        logging.warning(f"Utilisateur {user_id} introuvable dans la base, recréation...")
        scores_table.insert({
            'user_id': user_id,
            'score': 0,
            'stats_company': 0,
            'stats_team': 0,
            'stats_name': 0,
            'stats_position': 0,
            'total_correct_answers': 0
        })


def store_data_in_db(data):
    data_id = random.randint(1000, 9999)
    db.table('game_data').insert({'data_id': data_id, 'data': data})
    return data_id


def get_data_from_db(data_id):
    data_entry = db.table('game_data').get(Query().data_id == data_id)
    return data_entry['data']


if __name__ == '__main__':
    app.run(debug=True)