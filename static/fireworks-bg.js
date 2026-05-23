/* fireworks-bg.js — looping firework backdrop, palette-agnostic.
 *
 * Always loaded by base templates so the wizard can flip the bg
 * effect at runtime without re-fetching scripts. Auto-starts only
 * if `data-bg-effect="fireworks"` was set on <html> at parse time;
 * otherwise it stays idle and waits for particles-init.js to call
 * `__fireworksBgStart` (e.g. after a wizard radio change).
 *
 * Public API:
 *   window.__fireworksBgStart()  — kick off the loop
 *   window.__fireworksBgStop()   — tear down + remove the canvas
 *   window.__fireworksBgLaunch(x, y) — fire a single burst at a point
 *                                      (used by the Konami easter egg)
 *
 * Honors `prefers-reduced-motion: reduce` (start() is a no-op).
 * Pauses on `visibilitychange` so background tabs stay quiet.
 */
(function () {
    if (typeof window === 'undefined' || typeof document === 'undefined') return;

    const SPARK_COLORS = [
        'rgba(255, 0, 0, 0.85)',
        'rgba(0, 255, 0, 0.85)',
        'rgba(0, 0, 255, 0.85)',
        'rgba(255, 255, 0, 0.85)',
        'rgba(255, 0, 255, 0.85)',
        'rgba(0, 255, 255, 0.85)',
        'rgba(255, 215, 0, 0.85)',
        'rgba(255, 255, 255, 0.85)',
    ];

    function hexToTrail(hex) {
        const m = /^#([0-9a-f]{6})$/i.exec(hex);
        if (!m) return 'rgba(10, 14, 39, 0.18)';
        const n = parseInt(m[1], 16);
        return `rgba(${(n >> 16) & 255}, ${(n >> 8) & 255}, ${n & 255}, 0.18)`;
    }

    function reduced() {
        return window.matchMedia
            && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    }

    let canvas = null;
    let ctx = null;
    let particles = [];
    let lastLaunch = 0;
    let raf = 0;
    let visListener = null;
    let resizeListener = null;
    let trailFill = 'rgba(10, 14, 39, 0.18)';

    function fit() {
        if (!canvas || !ctx) return;
        const dpr = Math.min(window.devicePixelRatio || 1, 2);
        canvas.width = Math.floor(window.innerWidth * dpr);
        canvas.height = Math.floor(window.innerHeight * dpr);
        canvas.style.width = window.innerWidth + 'px';
        canvas.style.height = window.innerHeight + 'px';
        ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    }

    function launchFirework(xCss, yCss) {
        if (!canvas) return;
        const w = window.innerWidth;
        const h = window.innerHeight;
        const x = xCss != null ? xCss : Math.random() * (w * 0.8) + w * 0.1;
        const y = yCss != null ? yCss : Math.random() * (h * 0.4) + h * 0.15;
        const color = SPARK_COLORS[Math.floor(Math.random() * SPARK_COLORS.length)];
        const sparks = 28 + Math.floor(Math.random() * 12);
        for (let i = 0; i < sparks; i++) {
            const angle = (i / sparks) * Math.PI * 2 + Math.random() * 0.1;
            const speed = 2 + Math.random() * 4;
            particles.push({
                x, y,
                vx: Math.cos(angle) * speed,
                vy: Math.sin(angle) * speed,
                life: 1,
                decay: 0.012 + Math.random() * 0.012,
                size: 1.6 + Math.random() * 1.4,
                color,
            });
        }
    }

    function tick() {
        if (!ctx) return;
        const w = window.innerWidth;
        const h = window.innerHeight;
        ctx.fillStyle = trailFill;
        ctx.fillRect(0, 0, w, h);

        const now = performance.now();
        if (now - lastLaunch > 1400 + Math.random() * 1200) {
            launchFirework();
            lastLaunch = now;
        }

        for (const p of particles) {
            if (p.life <= 0) continue;
            p.vy += 0.05;
            p.vx *= 0.99;
            p.vy *= 0.99;
            p.x += p.vx;
            p.y += p.vy;
            p.life -= p.decay;
            ctx.beginPath();
            ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
            ctx.fillStyle = p.color;
            ctx.globalAlpha = Math.max(0, p.life);
            ctx.fill();
        }
        ctx.globalAlpha = 1;
        if (particles.length > 600) {
            particles = particles.filter((p) => p.life > 0);
        }
        raf = requestAnimationFrame(tick);
    }

    function start() {
        if (reduced()) return;
        if (canvas) return;  // already running

        const container = document.getElementById('particles-bg-container');
        if (!container) return;
        canvas = document.createElement('canvas');
        canvas.style.cssText = 'position:absolute; inset:0; width:100%; height:100%;';
        container.appendChild(canvas);
        ctx = canvas.getContext('2d');
        if (!ctx) {
            canvas.remove();
            canvas = null;
            return;
        }

        // Recompute trail tint each start so palette switches stick.
        const styles = getComputedStyle(document.documentElement);
        const bgRaw = (styles.getPropertyValue('--bg') || '#0A0E27').trim();
        trailFill = hexToTrail(bgRaw);

        particles = [];
        fit();
        lastLaunch = performance.now();
        tick();

        resizeListener = fit;
        visListener = () => {
            if (document.hidden) {
                cancelAnimationFrame(raf);
                raf = 0;
            } else if (!raf) {
                lastLaunch = performance.now();
                tick();
            }
        };
        window.addEventListener('resize', resizeListener);
        document.addEventListener('visibilitychange', visListener);
    }

    function stop() {
        if (raf) {
            cancelAnimationFrame(raf);
            raf = 0;
        }
        if (resizeListener) {
            window.removeEventListener('resize', resizeListener);
            resizeListener = null;
        }
        if (visListener) {
            document.removeEventListener('visibilitychange', visListener);
            visListener = null;
        }
        if (canvas) {
            canvas.remove();
            canvas = null;
        }
        ctx = null;
        particles = [];
    }

    window.__fireworksBgStart = start;
    window.__fireworksBgStop = stop;
    window.__fireworksBgLaunch = launchFirework;

    // Don't auto-start here — particles-init.js is the orchestrator
    // and will call start() if the resolved effect is 'fireworks'.
})();
