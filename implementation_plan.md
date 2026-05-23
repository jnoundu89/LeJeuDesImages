# Plan d'implémentation : Refonte Visuelle & Polish UX (Proposition 3)

Ce plan décrit les modifications à apporter au design du jeu pour offrir une esthétique moderne et interactive (effet de verre / glassmorphism, micro-animations Alpine.js, transitions fluides et ombres soignées).

## User Review Required

> [!NOTE]
> Toutes les modifications esthétiques s'appuient sur les tokens existants du design system (`design-tokens.css`). Nous n'ajoutons pas de variables globales supplémentaires pour préserver la portabilité et le fonctionnement des 16 palettes du sélecteur de thème.

## Proposed Changes

### [Axe 1 : Glassmorphism & Panneaux]

#### [MODIFY] [gameplay.css](file:///mnt/c/Users/yassi/PycharmProjects/PythonProject/LeJeuDesImages/static/gameplay.css)
* Remplacer le fond uni des 3 panneaux de jeu principaux (`.stats`, `.right-content`, `.center-content`) par un effet de verre transparent moderne :
  ```css
  background: color-mix(in srgb, var(--card-bg, var(--surface)) 82%, transparent);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid color-mix(in srgb, var(--border) 40%, transparent);
  box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.08);
  ```
* Ajouter des transitions globales sur toutes les actions interactives (survol, focus, clic) pour un rendu extrêmement fluide.

---

### [Axe 2 : Mode Selection & Hover Effects]

#### [MODIFY] [mode-selection.css](file:///mnt/c/Users/yassi/PycharmProjects/PythonProject/LeJeuDesImages/static/mode-selection.css)
* Améliorer le survol des cartes de jeu (`.mode-card`) :
  * Légère élévation en 3D (`transform: translateY(-4px) scale(1.025)`).
  * Lueur diffuse de la couleur primaire de l'entreprise (`box-shadow: 0 12px 24px var(--primary-ring)`).
  * Transition douce sur 0.3s avec une courbe de Bézier premium (`transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1)`).

---

### [Axe 3 : Alpine.js Transitions & Gameplay Animations]

#### [MODIFY] [base_game.html](file:///mnt/c/Users/yassi/PycharmProjects/PythonProject/LeJeuDesImages/templates/base_game.html)
* Ajouter des animations d'entrée Alpine.js (`x-transition`) sur les différents éléments dynamiques :
  * Bannière de statistiques (`.stats-banner`) : transition fluide en fondu/hauteur au dépliage.
  * Bouton "Personne suivante" (`#next`) : transition d'opacité et d'échelle (`scale`) lorsqu'il passe de l'état désactivé à activé.

#### [MODIFY] [game-alpine.js](file:///mnt/c/Users/yassi/PycharmProjects/PythonProject/LeJeuDesImages/static/game-alpine.js)
* Optimiser les contrôles d'état dans le store Alpine pour soutenir ces transitions sans à-coups visuels.

---

### [Axe 4 : Polish des boutons et du minuteur]

#### [MODIFY] [design-tokens.css](file:///mnt/c/Users/yassi/PycharmProjects/PythonProject/LeJeuDesImages/static/design-tokens.css)
* Ajuster les styles de boutons génériques pour intégrer un effet de brillance ou de lueur diffuse au survol (boutons `.btn-primary` et choix de jeu).

---

## Spécifications de Design Validées (Entretien /grill-me)

Suite à notre entretien interactif, les choix esthétiques suivants ont été validés et intégrés aux objectifs d'implémentation :
1. **Feedback de Réponse (Correcte/Incorrecte)** : Onde de choc lumineuse en CSS (ripple/glow pulse) autour du bouton cliqué + lueur diffuse de la couleur de statut (vert succès / rouge danger) sur tout le panneau de jeu central.
2. **Effet d'Urgence du Minuteur** : Effet d'horloge numérique rétro en police pixel (VT323) qui s'illumine et tremble légèrement (glitch/shake effect) à chaque seconde qui s'écoule dès que le temps passe sous la barre critique des 15 secondes.
3. **Transition entre les Questions** : Effet de flux continu de type "Card Slide" (la question en cours glisse doucement vers la gauche en s'estompant, et la nouvelle question glisse depuis la droite en fondu).
4. **Survol des Boutons de Choix** : Effet de balayage brillant (shimmer reflection) au survol, accompagné d'un léger agrandissement (scale 1.03) et d'un liseré néon de la couleur primaire.

## Verification Plan

### Automated Tests
- Relancer la suite complète de tests locaux pour s'assurer qu'aucune modification CSS ou HTML ne casse les sélecteurs requis par les tests E2E Playwright.
  ```bash
  make test
  ```

### Manual Verification
- Démarrer l'application locale :
  ```bash
  make run
  ```
- Naviguer sur `http://localhost:5000` et tester la fluidité des animations de survol des cartes.
- Lancer une partie en Mode Normal, observer l'effet de flou d'arrière-plan (glassmorphism) sur les colonnes gauche/droite et le comportement du bouton "Suivant" avec son animation Alpine.js.
