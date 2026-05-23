/* particles-init.js — orchestrates the animated backdrop.
 *
 * Picks the right effect from `data-bg-effect` on <html> on initial
 * load and exposes `window.applyBackgroundEffect(effect)` for runtime
 * swaps (used by the admin wizard's live preview).
 *
 * Two effects coexist on the same #particles-bg-container element:
 * - The vincentgarreau/particles.js library (vendored + 5 JSON
 *   presets under static/vendor/presets/) handles 'nasa', 'default',
 *   'snow', 'bubble', 'star'.
 * - Our custom canvas loop in static/fireworks-bg.js handles
 *   'fireworks'. It exposes __fireworksBgStart / __fireworksBgStop
 *   so we can flip between the two without a page reload.
 *
 * Honors `prefers-reduced-motion: reduce` (no animation initialised
 * on first load — but applyBackgroundEffect remains callable so the
 * wizard preview still works for users who haven't opted out).
 */
(function () {
    if (typeof window === 'undefined' || typeof document === 'undefined') return;

    const PARTICLES_PRESETS = ['nasa', 'default', 'snow', 'bubble', 'star'];
    // Aliases for legacy values that may still exist in saved configs.
    const ALIASES = { particles: 'nasa' };

    function reduced() {
        return window.matchMedia
            && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    }

    function teardown() {
        // 1) Stop any running particles.js instance(s).
        if (Array.isArray(window.pJSDom)) {
            window.pJSDom.forEach((d) => {
                try { d.pJS.fn.vendors.destroypJS(); } catch (_) { /* swallow */ }
            });
            window.pJSDom = [];
        }
        // 2) Stop our custom fireworks loop if it's running.
        if (typeof window.__fireworksBgStop === 'function') {
            try { window.__fireworksBgStop(); } catch (_) { /* swallow */ }
        }
        // 3) Empty the container so the next effect starts on a clean slate.
        const c = document.getElementById('particles-bg-container');
        if (c) c.innerHTML = '';
    }

    function resolveEffect(effect) {
        // Auto resolves to fireworks for legacy palette, nasa otherwise.
        if (effect === 'auto') {
            const palette = document.documentElement.dataset.palette;
            return palette === 'legacy' ? 'fireworks' : 'nasa';
        }
        if (ALIASES[effect]) return ALIASES[effect];
        if (effect === 'fireworks' || effect === 'none') return effect;
        if (PARTICLES_PRESETS.includes(effect)) return effect;
        return 'nasa';  // unknown → fall back to NASA
    }

    function apply(rawEffect) {
        const effect = resolveEffect(rawEffect);
        teardown();
        document.documentElement.dataset.bgEffect = effect;

        if (reduced() || effect === 'none') return;

        if (effect === 'fireworks') {
            if (typeof window.__fireworksBgStart === 'function') {
                window.__fireworksBgStart();
            }
            return;
        }

        if (typeof particlesJS !== 'function' || typeof particlesJS.load !== 'function') {
            console.warn('[particles-init] particles.js library not loaded; backdrop skipped.');
            return;
        }

        const url = '/static/vendor/presets/' + effect + '.json';
        particlesJS.load('particles-bg-container', url, function () {
            // No-op callback — the library logs its own status.
        });
    }

    window.applyBackgroundEffect = apply;

    // Initial bootstrap from the data attribute.
    apply(document.documentElement.dataset.bgEffect || 'nasa');
})();
