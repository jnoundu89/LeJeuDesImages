# Nouveaux Modes de Jeu pour "Le Jeu Des Images"

Ce document décrit les nouveaux modes de jeu amusants et créatifs ajoutés à l'application "Le Jeu Des Images".

## Modes de Jeu Ajoutés

### 1. Mode Visage Mélangé (Scrambled Face)

**Description**: Dans ce mode, les parties du visage (yeux, nez, bouche) sont mélangées avec celles d'autres employés. Les joueurs doivent identifier la personne malgré ce mélange.

**Fonctionnalités**:
- Affichage d'un visage dont les parties sont mélangées avec d'autres employés
- Bouton pour révéler le visage original
- Choix multiples pour identifier la personne

**Fichiers implémentés**:
- `models/scrambled_face_mode.py` - Logique du mode de jeu
- `templates/scrambled_face.html` - Interface utilisateur

### 2. Mode Défi Emoji (Emoji Challenge)

**Description**: Ce mode représente les caractéristiques d'un employé (entreprise, équipe, poste) par des emojis. Les joueurs doivent deviner qui est la personne à partir de ces indices.

**Fonctionnalités**:
- Affichage d'emojis représentant l'entreprise, l'équipe et le poste
- Emojis de personnalité générés en fonction des caractéristiques de l'employé
- Bouton pour révéler la photo de l'employé
- Choix multiples pour identifier la personne

**Fichiers implémentés**:
- `models/emoji_challenge_mode.py` - Logique du mode de jeu
- `templates/emoji_challenge.html` - Interface utilisateur

### 3. Mode Silhouette (Silhouette)

**Description**: Dans ce mode, seule la silhouette noire de l'employé est visible. Les joueurs doivent identifier la personne à partir de sa silhouette, avec l'aide d'un indice.

**Fonctionnalités**:
- Affichage de la silhouette noire de l'employé
- Indice sur l'équipe ou le poste de l'employé
- Bouton pour révéler la photo originale
- Choix multiples pour identifier la personne

**Fichiers implémentés**:
- `models/silhouette_mode.py` - Logique du mode de jeu
- `templates/silhouette.html` - Interface utilisateur

### 4. Mode Miroir (Mirror)

**Description**: Ce mode affiche l'image de l'employé inversée horizontalement (effet miroir). Cela peut être étonnamment difficile car notre cerveau est habitué à voir les visages dans une orientation spécifique.

**Fonctionnalités**:
- Affichage de l'image inversée horizontalement
- Faits amusants sur la perception des visages en miroir
- Bouton pour basculer entre l'image inversée et normale
- Choix multiples pour identifier la personne

**Fichiers implémentés**:
- `models/mirror_mode.py` - Logique du mode de jeu
- `templates/mirror.html` - Interface utilisateur

## Comment Jouer

1. Accédez à la page de sélection des modes de jeu
2. Choisissez l'un des nouveaux modes de jeu
3. Suivez les instructions à l'écran pour jouer
4. Essayez d'identifier correctement les employés pour augmenter votre score

## Caractéristiques Communes

Tous les nouveaux modes de jeu incluent:
- Un chronomètre de 60 secondes par question
- Des statistiques de jeu accessibles via un bouton
- Une barre de progression pour suivre votre avancement
- Des animations et effets visuels pour une expérience plus immersive
- Un système de score qui récompense les bonnes réponses

## Implémentation Technique

Les nouveaux modes de jeu ont été implémentés en suivant l'architecture existante:
1. Création de classes héritant de `GameMode` dans le dossier `models/`
2. Création de templates HTML dans le dossier `templates/`
3. Enregistrement des modes dans `app.py` via `GameModeFactory`

Chaque mode utilise CSS et JavaScript pour créer des effets visuels uniques et une expérience utilisateur engageante.