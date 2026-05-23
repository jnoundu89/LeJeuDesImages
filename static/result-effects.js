/* result-effects.js — count-up + confetti reward on the result page.
 *
 * Reads target / max from data attributes on `.result-score`. Both
 * effects bail out under prefers-reduced-motion (count-up displays
 * the final value immediately; confetti doesn't render at all).
 */
(function () {
    if (typeof window === 'undefined' || typeof document === 'undefined') return;

    const reduce = window.matchMedia
        && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    const scoreEl = document.querySelector('[data-result-score]');
    if (!scoreEl) return;
    const target = Number(scoreEl.dataset.resultScore);
    const maxScore = Number(scoreEl.dataset.resultMax);
    const valueEl = scoreEl.querySelector('[data-result-score-value]');
    if (!valueEl || Number.isNaN(target)) return;

    // 1) Count-up animation -------------------------------------------
    if (reduce || target === 0) {
        valueEl.textContent = String(target);
    } else {
        const duration = Math.min(1200, Math.max(450, target * 35));
        const startedAt = performance.now();
        function step(now) {
            const t = Math.min(1, (now - startedAt) / duration);
            // ease-out cubic: starts fast, settles into the final value
            const eased = 1 - Math.pow(1 - t, 3);
            valueEl.textContent = String(Math.round(target * eased));
            if (t < 1) requestAnimationFrame(step);
            else valueEl.textContent = String(target);
        }
        requestAnimationFrame(step);
    }

    // 2) Confetti shower for ≥80% scores ------------------------------
    const ratio = maxScore > 0 ? target / maxScore : 0;
    if (reduce || ratio < 0.8) return;

    const canvas = document.createElement('canvas');
    canvas.className = 'result-confetti-canvas';
    canvas.setAttribute('aria-hidden', 'true');
    document.body.appendChild(canvas);
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    function fit() {
        canvas.width = Math.floor(window.innerWidth * dpr);
        canvas.height = Math.floor(window.innerHeight * dpr);
        canvas.style.width = window.innerWidth + 'px';
        canvas.style.height = window.innerHeight + 'px';
        ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    }
    fit();

    // Pull palette colors from CSS so confetti follows the dataset
    // theme (with a few brighter accents for a celebration vibe).
    const styles = getComputedStyle(document.documentElement);
    const primary = (styles.getPropertyValue('--primary') || '#4F46E5').trim();
    const colors = [primary, '#FACC15', '#EC4899', '#22D3EE', '#34D399', '#A78BFA'];

    const pieces = [];
    function spawnBurst() {
        const count = 80;
        const cx = window.innerWidth / 2;
        for (let i = 0; i < count; i++) {
            const angle = Math.random() * Math.PI - Math.PI / 2; // mostly upwards
            const speed = 6 + Math.random() * 7;
            pieces.push({
                x: cx + (Math.random() - 0.5) * 200,
                y: window.innerHeight - 40,
                vx: Math.cos(angle) * speed,
                vy: Math.sin(angle) * speed - 4,
                size: 6 + Math.random() * 6,
                rot: Math.random() * Math.PI * 2,
                vrot: (Math.random() - 0.5) * 0.3,
                color: colors[Math.floor(Math.random() * colors.length)],
                life: 1,
            });
        }
    }
    spawnBurst();
    // Two follow-up bursts for a more celebratory feel.
    setTimeout(spawnBurst, 250);
    setTimeout(spawnBurst, 550);

    let raf = 0;
    function tick() {
        ctx.clearRect(0, 0, window.innerWidth, window.innerHeight);
        let alive = 0;
        for (const p of pieces) {
            if (p.life <= 0) continue;
            alive++;
            p.vy += 0.18;     // gravity
            p.vx *= 0.995;    // air drag
            p.x += p.vx;
            p.y += p.vy;
            p.rot += p.vrot;
            p.life -= 0.005;
            ctx.save();
            ctx.translate(p.x, p.y);
            ctx.rotate(p.rot);
            ctx.fillStyle = p.color;
            ctx.globalAlpha = Math.max(0, p.life);
            ctx.fillRect(-p.size / 2, -p.size / 2, p.size, p.size * 0.45);
            ctx.restore();
        }
        ctx.globalAlpha = 1;
        if (alive > 0) {
            raf = requestAnimationFrame(tick);
        } else {
            cancelAnimationFrame(raf);
            canvas.remove();
        }
    }
    tick();

    window.addEventListener('resize', fit);
})();
