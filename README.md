# Le Jeu Des Images 🎮

Un jeu interactif pour identifier les membres de l'équipe Infolegale et Eloficash. Testez votre connaissance des collègues et amusez-vous à reconnaître qui est qui !

## 🚀 Installation

Pour installer et exécuter le jeu, suivez ces étapes simples :

1. **Clonez le dépôt** 📋
   ```bash
   git clone https://github.com/votre-utilisateur/LeJeuDesImages.git
   cd LeJeuDesImages
   ```

2. **Créez un environnement virtuel** 🔮
   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate

   # macOS/Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Installez les dépendances** 📦
   ```bash
   pip install -r requirements.txt
   ```

## 🎯 Comment jouer

1. **Lancez l'application** 🚀
   ```bash
   python app.py
   ```

2. **Ouvrez votre navigateur** 🌐
   Accédez à `http://127.0.0.1:5000` dans votre navigateur préféré.

3. **Choisissez un mode de jeu** 🎲
   - **Mode Normal** : Identifiez l'entreprise, l'équipe, le nom et le poste à partir d'une photo
   - **Mode Reverse** : Identifiez la personne à partir d'un nom
   - **Mode Example** : Un mode simplifié pour vous familiariser avec le jeu

4. **Répondez aux questions** ❓
   - Vous avez 60 secondes pour répondre à chaque question
   - Chaque bonne réponse vous rapporte des points
   - Essayez d'obtenir le meilleur score possible !

5. **Consultez vos résultats** 🏆
   - À la fin du jeu, vous verrez votre score final
   - Vous pouvez recommencer pour améliorer votre score

## 🧠 Astuces
- Prenez le temps d'observer attentivement les photos
- Mémorisez les visages et les noms pour améliorer votre score
- Jouez régulièrement pour mieux connaître vos collègues

## 🏗️ Architecture

Le projet a été refactorisé pour suivre une architecture modulaire avec une séparation claire des responsabilités. Voici les principaux composants :

### Modèles

- **EmployeeData** : Gère l'accès aux données des employés.
- **ScoreManager** : Gère les scores des utilisateurs.
- **GameManager** : Gère la logique du jeu.
- **GameMode** : Interface abstraite pour les modes de jeu.
  - **NormalMode** : Mode de jeu normal où l'utilisateur identifie l'entreprise, l'équipe, le nom et le poste à partir d'une image.
  - **ReverseMode** : Mode de jeu inversé où l'utilisateur identifie la personne à partir d'un nom.
- **GameModeFactory** : Fabrique pour créer et gérer les modes de jeu.

### Routes

- **game_routes** : Gère les routes Flask pour le jeu.

### Templates

- **mode_selection.html** : Page de sélection du mode de jeu.
- **index.html** : Template pour le mode de jeu normal.
- **reverse.html** : Template pour le mode de jeu inversé.
- **result.html** : Page de résultats.

## Comment ajouter un nouveau mode de jeu

Pour ajouter un nouveau mode de jeu, suivez ces étapes :

1. Créez une nouvelle classe qui hérite de `GameMode` dans `models/game_mode.py` :

```python
class NewMode(GameMode):
    @property
    def name(self) -> str:
        return "new_mode"

    @property
    def description(self) -> str:
        return "Description du nouveau mode de jeu"

    @property
    def template(self) -> str:
        return "new_mode.html"

    def initialize(self, user_id: Optional[int] = None) -> Dict[str, Any]:
        # Logique d'initialisation du mode de jeu
        pass

    def get_question_data(self, data_id: int, used_indices: List[int], 
                         current_question: int) -> Dict[str, Any]:
        # Logique pour obtenir les données de la question
        pass

    def update_score(self, user_id: int, **kwargs) -> None:
        # Logique pour mettre à jour le score
        pass
```

2. Ajoutez des méthodes spécifiques au mode de jeu dans `GameManager` si nécessaire.

3. Créez un nouveau template HTML pour le mode de jeu dans le dossier `templates`.

4. Enregistrez le nouveau mode de jeu dans `GameModeFactory` :

```python
# Dans app.py ou dans une fonction d'initialisation
game_mode_factory.register_mode(NewMode(game_manager))
```

## Structure du projet

```
LeJeuDesImages/
├── app.py                  # Point d'entrée de l'application
├── infolegale_team.csv     # Données des employés
├── scores_db.json          # Base de données des scores
├── models/                 # Modèles de données et logique métier
│   ├── __init__.py
│   ├── employee.py         # Gestion des données des employés
│   ├── score.py            # Gestion des scores
│   ├── game.py             # Logique du jeu
│   └── game_mode.py        # Modes de jeu
├── routes/                 # Routes Flask
│   ├── __init__.py
│   └── game_routes.py      # Routes pour le jeu
├── static/                 # Fichiers statiques
│   ├── scripts.js          # JavaScript
│   └── styles.css          # CSS
└── templates/              # Templates HTML
    ├── index.html          # Mode normal
    ├── mode_selection.html # Sélection du mode
    ├── result.html         # Résultats
    └── reverse.html        # Mode inversé
```

## Avantages de la nouvelle architecture

1. **Séparation des responsabilités** : Chaque composant a une responsabilité claire.
2. **Extensibilité** : Il est facile d'ajouter de nouveaux modes de jeu sans modifier le code existant.
3. **Maintenabilité** : Le code est plus facile à comprendre et à maintenir.
4. **Testabilité** : Les composants peuvent être testés indépendamment.
5. **Réutilisabilité** : Les composants peuvent être réutilisés dans d'autres projets.
