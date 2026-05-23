# Plan d'implémentation : Restructuration Ergonomique du Menu Principal (Modes de Jeu)

Ce document présente notre proposition de restructuration complète du menu de sélection des modes de jeu. L'objectif est d'éliminer la surcharge cognitive (cognitive overload) d'une grille plate uniforme en introduisant des catégories de jeux thématiques, une bannière héroïque mettant en valeur un défi vedette, des boutons filtres avancés (style iOS) et des indicateurs de difficulté et durée grandement clarifiés.

## User Review Required

> [!IMPORTANT]
> - **Catégorisation des Modes** : Nous regroupons les modes de jeu en 4 grandes familles claires et engageantes pour guider immédiatement les joueurs selon leurs envies :
>   1. 🌟 **Les Incontournables** : Modes classiques et équilibrés (Normal, Devinette, Quiz).
>   2. 👁️ **Défis Visuels** : Modes mystérieux basés sur la reconnaissance visuelle (Pixelisation, Silhouette, Visage Scrambled, Memory).
>   3. 💼 **RH & Carrière** : Modes axés sur la culture d'entreprise (Poste/Position Match, Seniority/Âge, Miroir, Indices).
>   4. ⚡ **Contre-la-Montre** : Modes rapides et dynamiques (Timed, Speed, Émojis).
> - **Défi Vedette du Jour (Featured Banner)** : Intégration d'un panneau héroïque interactif en haut du menu mettant en avant un mode de jeu phare avec son illustration 3D, pour donner envie de lancer une partie en un clic.
> - **Filtrage Intelligent des Modes Verrouillés (QoL)** : Ajout d'un interrupteur (switch style iOS) permettant aux joueurs de masquer instantanément les modes verrouillés (ceux nécessitant des colonnes CSV absentes dans le dataset actuel).

---

## Open Questions

> [!IMPORTANT]
> 1. **Tri par défaut** : Préférez-vous que les modes soient présentés sous forme d'**onglets interactifs** (un seul groupe visible à la fois, ex: Incontournables, Visuels, RH, etc.) ou sous forme de **sections déroulantes** empilées verticalement pour pouvoir tout parcourir d'un coup d'œil ?
> 2. **Mode Vedette** : Souhaitez-vous que le mode vedette affiché en haut soit statique (le "Mode Normal", parfait pour débuter) ou dynamique (sélectionné aléatoirement parmi les modes disponibles à chaque chargement) ?

---

## Proposed Changes

### [Composant : Menu de Sélection des Modes]

Nous allons réécrire l'agencement et l'ergonomie du menu de sélection des modes dans le template HTML et le fichier CSS associé :

#### [MODIFY] [mode_selection.html](file:///mnt/c/Users/yassi/PycharmProjects/PythonProject/LeJeuDesImages/templates/mode_selection.html)
- **Bannière Héroïque Vedette (Featured)** : Insérer un conteneur `.featured-challenge-banner` contenant le mode vedette avec une description détaillée et un aperçu 3D grand format.
- **Barre d'Onglets Thématiques (Category Tabs)** :
  - Créer un panneau de navigation à onglets avec Alpine.js (`activeCategory`).
  - Définir 4 onglets majeurs : `all` (Tous), `classics` (Incontournables), `visual` (Visuels), `career` (RH & Carrière), `speed` (Rapidité).
- **Interrupteur Modernisé pour les Modes Disponibles** : Remplacer le filtre standard par un magnifique switch style iOS ou bouton toggle pour filtrer les modes jouables immédiatement.
- **Badge de Difficulté Premium** : Remplacer les 3 points par des badges colorés SaaS (`.badge-difficulty-easy`, `.badge-difficulty-medium`, `.badge-difficulty-hard`) avec icônes de jauge distinctives.

#### [MODIFY] [mode-selection.css](file:///mnt/c/Users/yassi/PycharmProjects/PythonProject/LeJeuDesImages/static/mode-selection.css)
- **Featured Banner Styling** : Gradients de verre dépoli à fort contraste avec reflets néon, angles arrondis adoucis, et mise en valeur de la composition 3D interactive.
- **Category Tabs Styles** : Liens d'onglets premium avec indicateurs de sélection soulignés de manière dynamique (`transform: scaleX()`), micro-animations de hover.
- **Badges de Difficulté & Durée** : Pilules colorées très lisibles s'adaptant à la palette de couleurs du thème actif.

---

## Verification Plan

### Automated Tests
- Lancer les tests unitaires et d'intégration E2E pour valider que la navigation et les sélecteurs de cartes de modes (`.mode-card`, `[data-mode]`) restent pleinement opérationnels :
  ```bash
  make test
  make test-e2e
  ```

### Manual Verification
- Naviguer sur `http://localhost:5000/` pour parcourir la nouvelle interface.
- Vérifier le fonctionnement dynamique des filtres de catégorie en un clic, le toggle des modes verrouillés, et l'ergonomie générale du menu.
