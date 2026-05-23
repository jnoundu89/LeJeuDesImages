# Roadmap — suites du refresh UI + refactor

État après la série de commits `2c7d543 → 376e5f3`.
La roadmap initiale (35 items) est quasi-entièrement absorbée dans 16
commits ; il ne reste que les items 🔴 hors-scope session et deux 🟡
nécessitant une infra dédiée (minification pipeline, audit contraste
WCAG automatisé).

## Légende effort

- 🟢 **Petit** (≤ ½ jour)
- 🟡 **Moyen** (1-2 jours)
- 🔴 **Gros** (3+ jours)

---

## 1. Qualité & CI

- ✅ 🟢 **FR catalogue** complète (commit `ca6d0f7`)
- ✅ 🟢 **CI GitHub Actions** (`.github/workflows/ci.yml`)
- ✅ 🟡 **Tests E2E par mode** (commit `3436c9b`) — 21 tests paramétrés
- ✅ 🟢 **Cleanup photos orphelines** (commit `068699e`)

---

## 2. A11y & UX

- ✅ 🟢 **Skip link + focus ring mode-cards** (commit `7cb06be`)
- ✅ 🟢 **Dark mode** (commit `d66d046`)
- ✅ 🟢 **Keyboard nav flèches dans la grille** (commit `a768a9e`)
- ✅ 🟡 **Refactor complet du theming dataset** — `theme: {palette,
  overrides}` avec 16 palettes et 7 tokens éditables (bg, surface,
  surface-2, text, text-soft, border, primary). Nouveau step wizard
  dédié avec preview live + jauge contraste WCAG. Les overrides sont
  injectés en inline style sur `<html>` pour battre la cascade
  palette sans toucher `design-tokens.css`. Round-trip export/import
  préserve les overrides (test d'intégration dédié).
- ⬜ 🟡 **Audit contraste WCAG AA auto pour les éléments dérivés**.
  Le nouveau step Thème affiche déjà le ratio texte/surface côté
  wizard, mais d'autres combinaisons (primary-contrast vs primary,
  text vs bg) ne sont pas vérifiées. Alternative : un check au save
  côté serveur qui refuse les overrides sous 4.5:1.

---

## 3. Dataset & data-model

- ✅ 🟡 **Auto-détection mapping CSV + preview live** (commit `9fba54e`)
- ✅ 🟡 **Multi-langue framework** (commit `376e5f3`) —
  `BABEL_SUPPORTED_LOCALES="fr,en,es"` suffit, switcher boucle
  sur la liste.
- ✅ 🟡 **Import/export dataset** (commit `f1741b0`) — ZIP CSV +
  photos + manifest.json, routes `/setup/<id>/export` et
  `/setup/import`.
- ⬜ 🔴 **Historique des scores par employé identifié**. Nécessite une
  migration TinyDB (nouvelle dimension « employé deviné »). Ouvre la
  porte à des stats intéressantes (« quels collègues sont les moins
  reconnus ») mais c'est une PR dédiée.

---

## 4. Gameplay — nouveaux modes

- ⬜ 🟡 **Mode Trombinoscope** (liste plate filtrable).
- ⬜ 🟡 **Mode « Équipe par équipe »** (photo de groupe).
- ⬜ 🟢 **Daily challenge** (seed basé sur la date).
- ⬜ 🔴 **Multi-joueur temps réel** via flask-socketio — gros chantier
  (lobby, état partagé, UI temps réel).

Ces items ne sont pas bloquants ; ce sont des idées produit à
prioriser selon le feedback utilisateur.

---

## 5. Perf & infra

- ✅ 🟢 **Lazy-loading + placeholder fallback** (commit `65f9580`)
- ✅ 🟢 **Compression/optimisation photos à l'upload** (commit `fac6c96`)
- ✅ 🟢 **Cache busting** (commit `65f9580`) — `static_v(filename)`
- ⬜ 🟡 **Minification CSS/JS en prod**. Ajouter un step build
  (`cssnano` / `lightningcss` / `esbuild`) au Makefile sous
  `make build-static`. Gain estimé 40-50% sur les assets. Requiert
  Node dans le conteneur de build ou un hook via uv. Nice-to-have :
  l'app reste parfaitement fluide avec des CSS non-minifiés vu leur
  taille actuelle (~35 Ko cumulés).

---

## 6. Dette technique

- ✅ 🟡 **`position_match` flexible** (commit `b1b2826`) —
  `employees_per_round` / `total_rounds` ClassVar, `min_eligible`
  dérivé, clamp auto au dataset.
- ✅ 🟢 **Tags i18n** (commit `ca6d0f7`)
- ⬜ 🟢 **Tests modes contract : `max_score >= 0`**. Le test actuel
  exige `> 0`. Pour un dataset volontairement vide ça bloque — soit
  relâcher l'assertion, soit séparer en deux tests.
- ⬜ 🟢 **Animation de preview qui traîne au clic** (polish cosmétique).

---

## 7. Documentation

- ✅ 🟢 **CONTRIBUTING.md à jour** (commit `376e5f3`) — documente la
  metadata ClassVar et les 9 preview_types.
- ⬜ 🟢 **Screenshots pour le README** (nécessite intervention user
  avec un vrai dataset + capture).
- ⬜ 🟢 **Doc previews dans `.claude/memory/`** (utile pour l'agent
  Claude quand il ajoute un mode).

---

## 8. Sécurité

- ✅ 🟡 **Rate-limiting login** (commit `fac6c96`)
- ✅ 🟢 **Headers sécurité** (commit `fac6c96`) — CSP, X-Frame,
  X-Content-Type, Referrer, Permissions
- ✅ 🟡 **Upload photos : magic number + taille + resize**
  (commit `fac6c96`)
- ✅ 🟢 **Path traversal guard** — `_safe_under()` appliqué partout
- ✅ 🟢 **Rate-limit routes mutantes** (commit `a768a9e`) —
  60/minute sur save/delete/upload/employee CRUD/import/cleanup.

---

## 9. Remaining — hors scope session

| Item | Effort | Raison |
|---|---|---|
| Historique scores par employé | 🔴 | Schema TinyDB + migration |
| Multi-joueur temps réel | 🔴 | Socket.IO + infra + lobby UI |
| WCAG contrast audit étendu | 🟡 | Step Thème couvre texte/surface, reste primary-contrast etc. |
| Minification CSS/JS prod | 🟡 | Node pipeline dans build |
| Mode Trombinoscope | 🟡 | Nouveau mode complet |
| Mode Équipe-par-équipe | 🟡 | Nouveau mode complet |
| Daily challenge | 🟢 | Seed + classement table |
| Screenshots README | 🟢 | Nécessite captures manuelles |
| Doc preview_types `.claude/memory/` | 🟢 | 10 min à écrire |
| `max_score >= 0` test | 🟢 | 2 lignes à relâcher |
| Animation preview au clic | 🟢 | CSS sur pagehide |

Tout ce qui était « 🟢 actionable » est fait. Les 🟡 restants sont
techniquement des sprints courts mais nécessitent une décision
produit (quels nouveaux modes valent le coup) ou une infra à
monter (minification pipeline, audit contraste). Les 🔴 sont des
features à part entière : historique scores = modification schéma
TinyDB + UI stats, multi-joueur = WebSocket + lobby.

Le projet est dans un état solide : la dette technique initiale est
purgée, le back est déclaratif, le front est cohérent bout-en-bout,
la sécurité couvre les vecteurs classiques, et l'i18n est ouvert
à n-langues.
