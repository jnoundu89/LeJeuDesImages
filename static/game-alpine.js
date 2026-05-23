/**
 * Alpine.js game components for LeJeuDesImages.
 * Replaces game-engine.js with declarative, per-component state.
 */

// Lightweight confetti burst anchored on a DOM element (used for correct
// answers). 18 coloured circles fan out radially, then fade & remove.
function burstParticles(anchorEl, count = 18) {
    if (!anchorEl) return;
    const rect = anchorEl.getBoundingClientRect();
    const cx = rect.left + rect.width / 2;
    const cy = rect.top + rect.height / 2;
    const colors = ['#FFD700', '#FF6B6B', '#4ECDC4', '#45B7D1', '#9BE564', '#FFB6B9'];
    for (let i = 0; i < count; i++) {
        const p = document.createElement('div');
        const size = 6 + Math.random() * 6;
        p.style.cssText =
            'position:fixed;pointer-events:none;z-index:9999;' +
            `width:${size}px;height:${size}px;border-radius:50%;` +
            `background:${colors[i % colors.length]};` +
            `left:${cx}px;top:${cy}px;` +
            'transition:transform 0.9s cubic-bezier(0.17,0.67,0.42,1.15),opacity 0.9s ease-out;';
        document.body.appendChild(p);
        requestAnimationFrame(() => {
            const angle = (i / count) * Math.PI * 2 + Math.random() * 0.5;
            const dist = 60 + Math.random() * 90;
            p.style.transform = `translate(${Math.cos(angle) * dist}px, ${Math.sin(angle) * dist}px) scale(${0.6 + Math.random()})`;
            p.style.opacity = '0';
        });
        setTimeout(() => p.remove(), 1000);
    }
}

document.addEventListener('alpine:init', () => {

    // ---- Reusable game state store ----
    Alpine.store('game', {
        score: 0,
        maxScore: 0,
        answersCount: 0,
        correctAnswers: 0,
        totalQuestions: 0,
        currentQuestion: 0,

        init() {
            const el = (id) => document.getElementById(id);
            this.maxScore = parseInt(el('max-score')?.value) || 0;
            this.totalQuestions = parseInt(el('total-questions')?.value) || 0;
            this.currentQuestion = parseInt(el('current-question')?.value) || 0;
        },

        addScore(n) {
            this.score += n;
            this.correctAnswers += n;
        },

        get nextEnabled() {
            return this.answersCount > 0;
        }
    });

    // ---- Timer component ----
    Alpine.data('gameTimer', (seconds = 60) => ({
        remaining: seconds,
        interval: null,
        expired: false,
        label: '',

        init() {
            this.label = this.$el.dataset.label || 'Temps restant';
            this.start();
        },

        start() {
            this.interval = setInterval(() => {
                this.remaining--;
                if (this.remaining <= 0) {
                    this.remaining = 0;
                    this.expired = true;
                    clearInterval(this.interval);
                    // Auto-enable next button on timeout
                    Alpine.store('game').answersCount = 1;
                }
            }, 1000);
        },

        stop() {
            clearInterval(this.interval);
        },

        get display() {
            return this.label + ': ' + this.remaining + 's';
        },

        get isWarning() {
            return this.remaining <= 20 && this.remaining > 15;
        },

        get isDanger() {
            return this.remaining <= 15;
        },

        destroy() {
            clearInterval(this.interval);
        }
    }));

    // ---- Single-answer mode (most modes) ----
    Alpine.data('singleAnswer', (correctValue) => ({
        answered: false,
        correct: correctValue,

        check(selected, el) {
            if (this.answered) return;
            this.answered = true;

            const store = Alpine.store('game');
            const root = this.$root || this.$el.closest('[x-data]') || document;
            const buttons = root.querySelectorAll('button.choice-btn, button.normal-choice-btn, button.example-choice-btn');
            const centerPanel = document.querySelector('.center-content');

            // Disable all buttons
            buttons.forEach(btn => {
                btn.disabled = true;
                btn.classList.add('disabled-btn');
            });

            if (selected === this.correct) {
                el.classList.add('correct');
                store.addScore(1);
                document.getElementById('correct-answer').value = 1;
                burstParticles(el);
                centerPanel?.classList.add('correct-glow');
            } else {
                el.classList.add('incorrect');
                centerPanel?.classList.add('incorrect-glow');
                // Highlight correct answer
                buttons.forEach(btn => {
                    const text = btn.textContent.trim();
                    const val = btn.getAttribute('data-value') || btn.dataset.value;
                    const cleanText = text.replace(/\s+/g, ' ').trim().toLowerCase();
                    const correctLower = this.correct.replace(/\s+/g, ' ').trim().toLowerCase();
                    const valLower = val ? val.replace(/\s+/g, ' ').trim().toLowerCase() : '';
                    const altLower = btn.querySelector('img')?.alt?.replace(/\s+/g, ' ')?.trim()?.toLowerCase() || '';

                    if (cleanText === correctLower || 
                        valLower === correctLower || 
                        altLower === correctLower ||
                        cleanText === correctLower + ' ans' || 
                        cleanText === correctLower + ' an' ||
                        cleanText === correctLower + ' s') {
                        btn.classList.add('correct');
                    }
                });
            }

            store.answersCount = 1;
        }
    }));

    // ---- Image check mode (reverse, manager) ----
    Alpine.data('imageAnswer', (correctValue) => ({
        answered: false,
        correct: correctValue,

        check(selected, el) {
            if (this.answered) return;
            this.answered = true;

            const store = Alpine.store('game');
            const root = this.$root || this.$el.closest('[x-data]') || document;
            const buttons = root.querySelectorAll('.choice-btn');
            const centerPanel = document.querySelector('.center-content');

            buttons.forEach(btn => {
                btn.disabled = true;
                btn.style.opacity = '0.6';
            });

            if (selected === this.correct) {
                el.classList.add('correct');
                store.addScore(1);
                document.getElementById('correct-answer').value = 1;
                burstParticles(el);
                centerPanel?.classList.add('correct-glow');
            } else {
                el.classList.add('incorrect');
                centerPanel?.classList.add('incorrect-glow');
                buttons.forEach(btn => {
                    const altText = btn.querySelector('img')?.alt?.replace(/\s+/g, ' ')?.trim()?.toLowerCase();
                    const correctLower = this.correct.replace(/\s+/g, ' ').trim().toLowerCase();
                    if (altText === correctLower) {
                        btn.classList.add('correct');
                    }
                });
            }

            store.answersCount = 1;
        }
    }));

    // ---- Progress bar ----
    Alpine.data('progressBar', () => ({
        get percentage() {
            const store = Alpine.store('game');
            const total = store.totalQuestions || 1;
            const current = Math.max(1, store.currentQuestion);
            return Math.max(10, (current / total) * 100);
        },
        get text() {
            const store = Alpine.store('game');
            return store.currentQuestion + '/' + store.totalQuestions;
        }
    }));

    // ---- Stats toggle ----
    Alpine.data('statsToggle', () => ({
        open: false,
        toggle() { this.open = !this.open; }
    }));

    // ---- Normal mode (4-step sequential, one section at a time) ----
    Alpine.data('normalMode', (correctValues) => ({
        step: 0,
        parts: ['company', 'team', 'name', 'position'],
        correctValues: correctValues,
        totalCorrect: 0,

        checkStep(category, selected, el) {
            const correct = this.correctValues[category];
            const container = el.closest('.normal-choices') || el.parentElement;
            const buttons = container.querySelectorAll('button');
            const titleEl = document.getElementById(category + '-title');
            const labelStrong = titleEl ? titleEl.querySelector('strong') : null;
            const labelText = labelStrong ? labelStrong.outerHTML : category + ' :';
            const centerPanel = document.querySelector('.center-content');

            buttons.forEach(btn => {
                btn.disabled = true;
                btn.classList.add('disabled-btn');
            });

            if (selected === correct) {
                el.classList.add('correct');
                el.classList.remove('disabled-btn');
                this.totalCorrect++;
                document.getElementById(category + '-correct').value = 1;
                if (titleEl) titleEl.innerHTML = labelText + ' <span class="success-icon">\u2713</span> 1/1';
                burstParticles(el);
                centerPanel?.classList.add('correct-glow');
                setTimeout(() => centerPanel?.classList.remove('correct-glow'), 600);
            } else {
                el.classList.add('incorrect');
                centerPanel?.classList.add('incorrect-glow');
                setTimeout(() => centerPanel?.classList.remove('incorrect-glow'), 600);
                buttons.forEach(btn => {
                    const btnText = btn.textContent.replace(/\s+/g, ' ').trim().toLowerCase();
                    const correctLower = correct.replace(/\s+/g, ' ').trim().toLowerCase();
                    if (btnText === correctLower) {
                        btn.classList.add('correct');
                        btn.classList.remove('disabled-btn');
                    }
                });
                if (titleEl) titleEl.innerHTML = labelText + ' <span class="error-icon">\u2717</span> 0/1';
                container.classList.add('shake');
                setTimeout(() => container.classList.remove('shake'), 500);
            }

            // Update score display
            const store = Alpine.store('game');
            store.score = this.totalCorrect;

            // Advance to next step \u2014 cap at 3 so the last (position) section
            // stays visible with its feedback until the user clicks Next.
            const lastStep = this.parts.length - 1;
            setTimeout(() => {
                if (this.step < lastStep) {
                    this.step++;
                } else {
                    // All 4 answered; enable Next and persist score increment.
                    store.answersCount = this.parts.length;
                    document.getElementById('score-increment').value = this.totalCorrect;
                }
            }, 800);
        }
    }));

    // ---- Confetti effect ----
    Alpine.data('confetti', () => ({
        burst(el) {
            for (let i = 0; i < 15; i++) {
                const particle = document.createElement('div');
                particle.style.cssText = `position:fixed;width:8px;height:8px;border-radius:50%;pointer-events:none;z-index:9999;transition:all 0.8s ease-out;background:${['#FFD700','#FF6B6B','#4ECDC4','#45B7D1'][i%4]}`;
                const rect = el.getBoundingClientRect();
                particle.style.left = rect.left + rect.width/2 + 'px';
                particle.style.top = rect.top + rect.height/2 + 'px';
                document.body.appendChild(particle);
                setTimeout(() => {
                    const angle = Math.random() * Math.PI * 2;
                    const dist = 40 + Math.random() * 80;
                    particle.style.left = parseFloat(particle.style.left) + Math.cos(angle)*dist + 'px';
                    particle.style.top = parseFloat(particle.style.top) + Math.sin(angle)*dist + 'px';
                    particle.style.opacity = '0';
                }, 10);
                setTimeout(() => particle.remove(), 900);
            }
        }
    }));
});
