# Checklist : Refonte Visuelle & Polish UX

Suivi de l'implémentation de la Proposition 3 (Axe UX & Interface).

- `[x]` **Axe 1 : Design System & Tokens**
  - `[x]` Ajouter des variables de lueur et de shimmer dans `design-tokens.css`
  - `[x]` Optimiser les transitions par défaut
- `[x]` **Axe 2 : Effet de Verre & Panneaux (Glassmorphism)**
  - `[x]` Mettre à jour `gameplay.css` avec le backdrop-filter et les bordures semi-transparentes
  - `[x]` Ajouter l'onde de choc (ripple wave) et la lueur succès/danger au feedback de réponses
- `[x]` **Axe 3 : Survol Premium des Cartes**
  - `[x]` Ajouter l'élévation et la lueur de couleur primaire au survol des cartes dans `mode-selection.css`
- `[x]` **Axe 4 : Transitions Alpine.js & Chargement continu**
  - `[x]` Intégrer les animations de transition `x-transition` dans `base_game.html`
  - `[x]` Mettre en place l'effet "Card Slide" lors du changement de question
- `[x]` **Axe 5 : Minuteur d'Urgence Pixel Art & Glitch**
  - `[x]` Implémenter l'effet de secousse (shake/glitch) et le changement de police (VT323) sous les 15 secondes
- `[x]` **Axe 6 : Vérification & Polish final**
  - `[x]` Relancer la suite complète de tests locaux (`make test`)
  - `[/]` Relancer les E2E tests Playwright (`make test-e2e`) en contournant l'auth d'administration
