# Checklist : Refonte Ergonomique & Clarification du Menu Principal

Suivi des tâches pour réorganiser les modes de jeu par catégories et intégrer les optimisations UX/UI.

- `[x]` **Étape 1 : Refonte Structurelle (Jinja & HTML)**
  - `[x]` Intégrer la structure de la bannière vedette héroïque (`.featured-challenge-banner`) dans `templates/mode_selection.html`.
  - `[x]` Ajouter la structure de la barre d'onglets de catégories (`.category-navigation-tabs`) avec icônes.
  - `[x]` Ajouter l'interrupteur moderne style iOS pour basculer la visibilité des modes verrouillés.
  - `[x]` Mettre à jour l'affichage de la difficulté par des pilules de couleur SaaS (`.badge-difficulty`) et des icônes d'horloge harmonisés.
- `[x]` **Étape 2 : Polish Esthétique & Design System (CSS)**
  - `[x]` Styliser le panneau vedette héroïque avec reflets en verre néon dans `static/mode-selection.css`.
  - `[x]` Styliser les onglets de catégories avec transitions de soulignement dynamique au hover/actif.
  - `[x]` Créer les classes et styles des badges de difficulté SaaS (facile, moyen, difficile) et durée.
- `[x]` **Étape 3 : Logique de Filtrage Alpine.js**
  - `[x]` Associer chaque mode de jeu de la base de données à l'une des 4 catégories dans la structure de filtrage Alpine.
  - `[x]` Implémenter la réactivité des onglets avec `x-show` et `visibleCount` dans `modeSelection`.
- `[x]` **Étape 4 : Validation & Rendu**
  - `[x]` Valider avec la suite complète de tests unitaires (`make test`).
  - `[x]` Valider avec la suite complète de tests Playwright E2E (`make test-e2e`).
  - `[x]` Capturer les visuels de la nouvelle interface du menu de sélection des modes.
