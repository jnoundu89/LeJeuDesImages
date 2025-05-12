# Le Jeu Des Images 🎮

Un jeu interactif et ludique pour identifier les membres de l'équipe Infolegale et Eloficash. Testez votre connaissance des collègues et amusez-vous à reconnaître qui est qui !

![Version](https://img.shields.io/badge/version-2.0-blue)
![Python](https://img.shields.io/badge/Python-3.8%2B-brightgreen)
![Flask](https://img.shields.io/badge/Flask-2.0%2B-orange)

## 📋 Table des matières

- [Installation](#-installation)
- [Comment jouer](#-comment-jouer)
- [Modes de jeu](#-modes-de-jeu)
- [Nouveautés](#-nouveautés)
- [Design et expérience utilisateur](#-design-et-expérience-utilisateur)
- [Architecture](#-architecture)
- [Structure du projet](#-structure-du-projet)
- [Contribuer](#-contribuer)
- [Astuces](#-astuces)

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
   Sélectionnez parmi les nombreux modes de jeu disponibles.

4. **Répondez aux questions** ❓
   - Vous avez 60 secondes pour répondre à chaque question
   - Chaque bonne réponse vous rapporte des points
   - Profitez des animations et effets visuels qui rendent l'expérience plus immersive

5. **Consultez vos résultats** 🏆
   - À la fin du jeu, vous verrez votre score final avec des animations festives
   - Vous pouvez recommencer pour améliorer votre score

## 🎮 Modes de jeu

### Modes classiques
- **Mode Normal** : Identifiez l'entreprise, l'équipe, le nom et le poste à partir d'une photo
- **Mode Reverse** : Identifiez la personne à partir d'un nom
- **Mode Pixelisation** : Une image pixelisée qui devient progressivement plus nette

### Nouveaux modes créatifs
- **Mode Visage Mélangé** 🔀 : Les parties du visage (yeux, nez, bouche) sont mélangées avec celles d'autres employés
- **Mode Défi Emoji** 😎 : Devinez qui est la personne à partir d'emojis représentant ses caractéristiques
- **Mode Silhouette** 👤 : Identifiez la personne à partir de sa silhouette noire
- **Mode Miroir** 🪞 : L'image de l'employé est inversée horizontalement

### Modes avancés
- **Mode Quiz** 📝 : Répondez à des questions sur vos collègues
- **Mode Mémoire** 🧠 : Mémorisez les visages et retrouvez-les plus tard
- **Mode Équipe** 👥 : Identifiez tous les membres d'une équipe spécifique
- **Mode Indice Progressif** 🔍 : Recevez des indices progressifs pour identifier la personne
- **Mode Personne Disparue** 🕵️ : Retrouvez une personne "disparue" parmi plusieurs choix
- **Mode Correspondance de Poste** 📊 : Associez les personnes à leurs postes corrects
- **Mode Vitesse** ⚡ : Identifiez le plus de personnes possible dans un temps limité
- **Mode Chronométré** ⏱️ : Le temps diminue à chaque question
- **Mode Deviner l'Équipe** 🏢 : Identifiez à quelle équipe appartient une personne

## 🆕 Nouveautés

### Nouveaux modes de jeu
Nous avons ajouté plus de 10 nouveaux modes de jeu pour rendre l'expérience encore plus variée et amusante. Chaque mode offre une façon unique de tester votre connaissance des collègues.

### Caractéristiques communes à tous les modes
- Chronomètre de 60 secondes par question
- Statistiques de jeu accessibles via un bouton
- Barre de progression pour suivre votre avancement
- Animations et effets visuels pour une expérience plus immersive
- Système de score qui récompense les bonnes réponses

## 🎨 Design et expérience utilisateur

### Design moderne
- **Système de design cohérent** avec variables CSS pour les couleurs, l'espacement et la typographie
- **Typographie améliorée** avec la police Montserrat pour les titres
- **Palette de couleurs harmonieuse** avec couleurs primaires, secondaires et d'accent
- **Design responsive** adapté à tous les appareils

### Interface utilisateur améliorée
- **Design basé sur des cartes** avec ombres subtiles et effets au survol
- **Effets de glassmorphisme** pour un look contemporain
- **Espacement optimisé** pour une meilleure hiérarchie visuelle
- **Système de grille** plus réactif et adaptable

### Éléments interactifs
- **Système de boutons complet** avec plusieurs variations et états
- **Contrôles de formulaire améliorés** pour une meilleure utilisabilité
- **Barre de progression redessinée** avec animations fluides
- **Minuteur amélioré** avec indices visuels pour différents états

### Animations et transitions
- **Micro-interactions** pour un meilleur feedback
- **Transitions de page fluides** entre les différents états
- **Effets au survol améliorés** pour les éléments interactifs
- **Animation confetti** pour les bonnes réponses

## 🏗️ Architecture

Le projet suit une architecture modulaire avec une séparation claire des responsabilités :

### Modèles
- **EmployeeData** : Gère l'accès aux données des employés
- **ScoreManager** : Gère les scores des utilisateurs
- **GameManager** : Gère la logique du jeu
- **GameMode** : Interface abstraite pour les modes de jeu
- **GameModeFactory** : Fabrique pour créer et gérer les modes de jeu

### Routes
- **game_routes** : Gère les routes Flask pour le jeu

### Templates
- Templates HTML pour chaque mode de jeu
- Templates partagés pour les composants communs

## 📁 Structure du projet

```
LeJeuDesImages/
├── app.py                      # Point d'entrée de l'application
├── infolegale_team.csv         # Données des employés
├── scores_db.json              # Base de données des scores
├── models/                     # Modèles de données et logique métier
│   ├── employee.py             # Gestion des données des employés
│   ├── score.py                # Gestion des scores
│   ├── game.py                 # Logique du jeu
│   ├── game_mode.py            # Interface pour les modes de jeu
│   ├── normal_mode.py          # Mode de jeu normal
│   ├── reverse_mode.py         # Mode de jeu inversé
│   ├── pixelation_mode.py      # Mode pixelisation
│   ├── scrambled_face_mode.py  # Mode visage mélangé
│   ├── emoji_challenge_mode.py # Mode défi emoji
│   ├── silhouette_mode.py      # Mode silhouette
│   ├── mirror_mode.py          # Mode miroir
│   └── [autres modes de jeu]   # Autres modes de jeu
├── routes/                     # Routes Flask
│   ├── __init__.py
│   └── game_routes.py          # Routes pour le jeu
├── static/                     # Fichiers statiques
│   ├── scripts.js              # JavaScript principal
│   ├── animations.js           # Animations
│   ├── styles.css              # CSS principal
│   ├── animations.css          # Styles d'animation
│   └── [autres fichiers CSS/JS]# Autres ressources
└── templates/                  # Templates HTML
    ├── mode_selection.html     # Sélection du mode
    ├── normal.html             # Mode normal
    ├── reverse.html            # Mode inversé
    ├── pixelation.html         # Mode pixelisation
    ├── scrambled_face.html     # Mode visage mélangé
    ├── emoji_challenge.html    # Mode défi emoji
    ├── silhouette.html         # Mode silhouette
    ├── mirror.html             # Mode miroir
    ├── result.html             # Résultats
    └── [autres templates]      # Autres templates
```

## 🤝 Contribuer

### Comment ajouter un nouveau mode de jeu

1. Créez une nouvelle classe qui hérite de `GameMode` dans le dossier `models/` :

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

2. Créez un nouveau template HTML pour le mode de jeu dans le dossier `templates/`.

3. Enregistrez le nouveau mode de jeu dans `app.py` via `GameModeFactory`.

## 🧠 Astuces

- Prenez le temps d'observer attentivement les photos
- Mémorisez les visages et les noms pour améliorer votre score
- Essayez différents modes de jeu pour varier l'expérience
- Le mode Silhouette est plus facile si vous connaissez bien les silhouettes de vos collègues
- Dans le mode Emoji Challenge, faites attention aux emojis qui représentent l'équipe et le poste
- Pour le mode Miroir, essayez de vous concentrer sur les caractéristiques asymétriques du visage
- Jouez régulièrement pour mieux connaître vos collègues et améliorer votre score
