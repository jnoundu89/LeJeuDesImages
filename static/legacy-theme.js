/* legacy-theme.js — Konami code easter egg for the 'legacy' palette.
 *
 * Loaded by base_page.html only when the active dataset's palette
 * is 'legacy'. The fireworks backdrop itself moved to
 * static/fireworks-bg.js (palette-agnostic, gated by
 * `theme.background_effect` instead of palette).
 *
 * Konami sequence ↑↑↓↓←→←→ba triggers a golden radial flash plus a
 * coordinated cluster of fireworks across the viewport. We reuse the
 * fireworks-bg.js launcher via the `window.__fireworksBgLaunch`
 * hook when it's available; otherwise we settle for just the flash.
 */
(function () {
    if (typeof window === 'undefined' || typeof document === 'undefined') return;
    if (document.documentElement.dataset.palette !== 'legacy') return;

    const reduce = window.matchMedia
        && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    const KONAMI = [
        'ArrowUp', 'ArrowUp',
        'ArrowDown', 'ArrowDown',
        'ArrowLeft', 'ArrowRight',
        'ArrowLeft', 'ArrowRight',
        'b', 'a',
    ];
    let konamiIndex = 0;

    function flashGold() {
        const flash = document.createElement('div');
        flash.className = 'legacy-konami-flash';
        document.body.appendChild(flash);
        setTimeout(() => flash.remove(), 700);
    }

    function konamiBurst() {
        flashGold();
        if (reduce) return;
        const launch = window.__fireworksBgLaunch;
        if (typeof launch !== 'function') return;
        const cx = window.innerWidth / 2;
        const cy = window.innerHeight / 2;
        const points = [
            [cx, cy - 80],
            [cx - 150, cy + 30],
            [cx + 150, cy + 30],
            [cx, cy - 200],
            [cx - 250, cy - 50],
            [cx + 250, cy - 50],
        ];
        points.forEach(([x, y], idx) => {
            setTimeout(() => launch(x, y), idx * 120);
        });
    }

    document.addEventListener('keydown', (e) => {
        const expected = KONAMI[konamiIndex];
        if (e.key === expected) {
            konamiIndex++;
            if (konamiIndex === KONAMI.length) {
                konamiBurst();
                konamiIndex = 0;
            }
        } else {
            konamiIndex = e.key === KONAMI[0] ? 1 : 0;
        }
    });
})();
