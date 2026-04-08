// GameEngine - Consolidated game logic for LeJeuDesImages
// Single source of truth for answer checking, timer, progress, confetti, and UI helpers.
var GameEngine = (function() {
    'use strict';

    // --------------- Private state ---------------
    var _state = {
        answersCount: 0,
        correctAnswers: 0,
        currentScore: 0,
        maxScore: 0,
        timerValue: 60,
        timerInterval: null,
        totalQuestions: 0,
        pageJustLoaded: true
    };

    // --------------- Private helpers ---------------

    function _getOrCreateConfettiContainer() {
        var container = document.getElementById('confetti-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'confetti-container';
            container.style.position = 'fixed';
            container.style.top = '0';
            container.style.left = '0';
            container.style.width = '100%';
            container.style.height = '100%';
            container.style.pointerEvents = 'none';
            container.style.zIndex = '9999';
            document.body.appendChild(container);
        }
        return container;
    }

    function _spawnParticles(centerX, centerY, count, distance, duration, colors) {
        var container = _getOrCreateConfettiContainer();
        colors = colors || ['#ff0000', '#00ff00', '#0000ff', '#ffff00', '#ff00ff', '#00ffff'];

        for (var i = 0; i < count; i++) {
            var confetti = document.createElement('div');
            confetti.style.position = 'absolute';
            confetti.style.width = '10px';
            confetti.style.height = '10px';
            confetti.style.backgroundColor = colors[Math.floor(Math.random() * colors.length)];
            confetti.style.borderRadius = count > 50 ? (Math.random() > 0.5 ? '50%' : '0') : '50%';
            confetti.style.left = centerX + 'px';
            confetti.style.top = centerY + 'px';
            confetti.style.transform = 'translate(-50%, -50%)';
            confetti.style.opacity = '1';
            confetti.style.transition = 'all ' + (duration / 1000) + 's ease-out';

            container.appendChild(confetti);

            // Animate outward
            (function(el) {
                setTimeout(function() {
                    var angle = Math.random() * Math.PI * 2;
                    var dist = (distance * 0.5) + Math.random() * distance;
                    el.style.left = (centerX + Math.cos(angle) * dist) + 'px';
                    el.style.top = (centerY + Math.sin(angle) * dist) + 'px';
                    el.style.opacity = '0';
                    if (count > 50) {
                        el.style.transform = 'translate(-50%, -50%) rotate(' + (Math.random() * 360) + 'deg)';
                    }
                }, 10);

                setTimeout(function() {
                    if (container.contains(el)) {
                        container.removeChild(el);
                    }
                }, duration);
            })(confetti);
        }
    }

    // --------------- Public API ---------------
    var api = {};

    // -- Initialization --

    api.init = function(options) {
        options = options || {};
        _state.answersCount = 0;
        _state.correctAnswers = 0;
        _state.pageJustLoaded = true;

        // Parse current score from DOM
        var currentScoreElement = document.getElementById('current-score');
        if (currentScoreElement) {
            var scoreText = currentScoreElement.textContent;
            if (scoreText) {
                var scoreParts = scoreText.split(' ');
                if (scoreParts.length >= 5) {
                    _state.currentScore = parseInt(scoreParts[2]) || 0;
                    _state.maxScore = parseInt(scoreParts[4]) || 0;
                }
            }
        }

        // Parse max score from hidden inputs
        var maxScoreElement = document.getElementById('maxScore')
            || document.getElementById('max-score')
            || document.getElementById('max_score');
        var totalQuestionsElement = document.getElementById('total_questions')
            || document.getElementById('total-questions');

        if (maxScoreElement) {
            var maxScoreValue = parseInt(maxScoreElement.value) || 0;
            if (_state.maxScore === 0 && maxScoreValue > 0) {
                _state.maxScore = maxScoreValue;
            }
        }

        if (totalQuestionsElement) {
            _state.totalQuestions = parseInt(totalQuestionsElement.value) || 0;
        }

        // Update progress bar
        var progressBarFill = document.querySelector('.progress-bar-fill');
        if (progressBarFill && totalQuestionsElement && maxScoreElement) {
            api.updateProgressBar(
                parseInt(totalQuestionsElement.value) || 0,
                (_state.maxScore) / 4
            );
        }

        // Reset answers if on game page
        if (document.getElementById('next')) {
            api.resetAnswersCount();
        }

        // Initialize stats as hidden
        var statsBanner = document.getElementById('stats-banner');
        var toggleButton = document.querySelector('.toggle-stats-btn');
        if (statsBanner) {
            statsBanner.style.display = 'none';
            if (toggleButton) {
                toggleButton.textContent = 'Afficher les statistiques';
            }
        }
    };

    // -- Answer checking (normal 4-category mode) --

    api.checkAnswer = function(correct, selected, element, currentScoreId, titleId) {
        element.classList.add('processing');

        setTimeout(function() {
            element.classList.remove('processing');

            // Disable all buttons in this category
            var buttons = document.querySelectorAll('#' + currentScoreId + ' button.choice-btn, #' + currentScoreId + ' button.normal-choice-btn');
            buttons.forEach(function(btn) {
                btn.disabled = true;
                btn.classList.add('disabled-btn');
            });

            var titleEl = document.getElementById(titleId);
            var labelStrong = titleEl ? titleEl.querySelector('strong') : null;
            var labelText = labelStrong ? labelStrong.outerHTML : titleId.split('-')[0] + ' :';

            if (correct === selected) {
                element.classList.add('correct');
                element.classList.remove('disabled-btn');

                if (titleEl) {
                    titleEl.innerHTML =
                        labelText + ' <span class="success-icon">\u2713</span> 1/1';
                }

                _state.correctAnswers += 1;
                _state.currentScore += 1;

                api.createConfetti(element);
            } else {
                element.classList.add('incorrect');

                buttons.forEach(function(btn) {
                    if (btn.textContent === correct) {
                        btn.classList.add('correct');
                        btn.classList.remove('disabled-btn');
                    }
                });

                if (titleEl) {
                    titleEl.innerHTML =
                        labelText + ' <span class="error-icon">\u2717</span> 0/1';
                }
            }

            // Update score display
            var scoreElement = document.getElementById('current-score');
            if (scoreElement) {
                scoreElement.classList.add('score-updated');
                var displayCurrentScore = isNaN(_state.currentScore) ? 0 : _state.currentScore;
                var displayMaxScore = isNaN(_state.maxScore) ? 0 : _state.maxScore;
                var _scoreLabel = scoreElement.getAttribute('data-label') || 'Score actuel';
                scoreElement.textContent = _scoreLabel + ' : ' + displayCurrentScore + ' / ' + displayMaxScore;
            }

            if (scoreElement) {
                setTimeout(function() {
                    if (scoreElement) {
                        scoreElement.classList.remove('score-updated');
                    }
                }, 1000);
            }

            _state.answersCount += 1;
            if (_state.answersCount === 4) {
                api.enableNextButton();
                clearInterval(_state.timerInterval);
            }
        }, 300);
    };

    // -- Image checking (reverse mode) --

    api.checkImage = function(correct, selected, element) {
        var isReverseMode = document.getElementById('image-choices') !== null;
        var buttonSelector = isReverseMode ? '#image-choices .choice-btn' : '.choice-btn';
        var buttons = document.querySelectorAll(buttonSelector);

        buttons.forEach(function(btn) {
            btn.disabled = true;
            if (isReverseMode) {
                btn.style.opacity = '0.6';
            }
        });

        if (correct === selected) {
            element.classList.add('correct');
            _state.correctAnswers += 1;
            _state.currentScore += 1;
            document.getElementById('correct-answer').value = 1;
        } else {
            element.classList.add('incorrect');
            buttons.forEach(function(btn) {
                var img = btn.querySelector('img');
                if (img && img.alt === correct) {
                    btn.classList.add('correct');
                }
            });
        }

        if (isReverseMode) {
            _state.answersCount = 1;
            var scoreElement = document.getElementById('current-score');
            if (scoreElement) {
                var displayCurrentScore = isNaN(_state.currentScore) ? 0 : _state.currentScore;
                var displayMaxScore = isNaN(_state.maxScore) ? 0 : _state.maxScore;
                scoreElement.innerHTML = 'Score actuel : <span class="score">' + displayCurrentScore + ' / ' + displayMaxScore + '</span>';
            }
        } else {
            _state.answersCount += 1;
            var scoreEl = document.getElementById('current-score');
            if (scoreEl) {
                var dcs = isNaN(_state.currentScore) ? 0 : _state.currentScore;
                var dms = isNaN(_state.maxScore) ? 0 : _state.maxScore;
                scoreEl.textContent = 'Score actuel : ' + dcs + ' / ' + dms;
            }
        }

        if (_state.answersCount === 1 || (isReverseMode && _state.answersCount === 1)) {
            api.enableNextButton();
            clearInterval(_state.timerInterval);
        }
    };

    // -- Timer --

    api.startTimer = function(seconds, onExpire) {
        _state.timerValue = seconds || 60;
        api.updateTimer();
        clearInterval(_state.timerInterval);

        var timerElement = document.getElementById('timer');
        if (timerElement) {
            timerElement.classList.remove('game-over');
        }

        _state.timerInterval = setInterval(function() {
            _state.timerValue--;
            api.updateTimer();
            if (_state.timerValue <= 0) {
                clearInterval(_state.timerInterval);
                if (typeof onExpire === 'function') {
                    onExpire();
                } else {
                    if (_state.answersCount < 4) {
                        api.disableAllButtons();
                    }
                    api.enableNextButton();
                }
            }
        }, 1000);
    };

    api.updateTimer = function() {
        var timerElement = document.getElementById('timer');
        if (!timerElement) return;

        timerElement.classList.remove('warning', 'danger');

        var _timerLabel = timerElement.getAttribute('data-label') || 'Temps restant';

        if (_state.timerValue > 0) {
            timerElement.textContent = _timerLabel + ': ' + _state.timerValue + 's';

            if (_state.timerValue <= 20 && _state.timerValue > 10) {
                timerElement.classList.add('warning');
            } else if (_state.timerValue <= 10) {
                timerElement.classList.add('danger');
            }
        } else {
            timerElement.textContent = _timerLabel.replace(/restant|remaining/i, '') + '- 0s';
            timerElement.classList.add('danger');
        }
    };

    api.stopTimer = function() {
        clearInterval(_state.timerInterval);
    };

    // -- Progress bar --

    api.updateProgressBar = function(current, total) {
        var progressBarFill = document.querySelector('.progress-bar-fill');
        if (!progressBarFill) return;

        current = parseInt(current) || 0;
        total = parseInt(total) || 1;

        var displayCurrent = Math.max(1, current);
        var percentage = (displayCurrent / total) * 100;
        progressBarFill.style.width = Math.max(10, percentage) + '%';

        progressBarFill.style.color = 'white';
        progressBarFill.style.fontWeight = 'bold';
        progressBarFill.style.textShadow = '1px 1px 2px rgba(0, 0, 0, 0.7)';
        progressBarFill.textContent = displayCurrent + '/' + Math.round(total);
    };

    // -- UI helpers --

    api.resetAnswersCount = function() {
        _state.answersCount = 0;
        _state.correctAnswers = 0;
        var nextButton = document.getElementById('next');
        if (nextButton) {
            nextButton.disabled = true;
            nextButton.classList.add('disabled-btn');
        }
        api.startTimer(60);
    };

    api.enableNextButton = function() {
        var nextButton = document.getElementById('next');
        if (!nextButton) return;

        nextButton.disabled = false;
        nextButton.classList.remove('disabled-btn');

        var scoreIncrementEl = document.getElementById('score-increment');
        if (scoreIncrementEl) {
            scoreIncrementEl.value = _state.correctAnswers;
        }

        var timerElement = document.getElementById('timer');
        if (timerElement) {
            timerElement.classList.add('game-over');
        }

        clearInterval(_state.timerInterval);

        // Determine whether to show celebration confetti or shake
        var isReverseMode = document.getElementById('image-choices') !== null;
        var isPixelationMode = document.getElementById('pixelated-image') !== null;
        var correctAnswerEl = document.getElementById('correct-answer');
        var isCorrectAnswer = correctAnswerEl && correctAnswerEl.value === '1';

        var showConfetti = false;

        if (isReverseMode) {
            showConfetti = isCorrectAnswer;
        } else {
            showConfetti = _state.correctAnswers === 4;
        }

        if (!isReverseMode && !document.querySelector('.normal-choices')) {
            showConfetti = _state.correctAnswers > 0;
        }

        if (showConfetti) {
            var centerX = window.innerWidth / 2;
            var centerY = window.innerHeight / 2;
            _spawnParticles(centerX, centerY, 100, 200, 1500);
        } else if (!(isPixelationMode && isCorrectAnswer)) {
            api.shakeElement(document.body);
        }

        nextButton.scrollIntoView({ behavior: 'smooth', block: 'center' });
    };

    api.disableAllButtons = function(container) {
        var scope = container || document;
        var buttons = scope.querySelectorAll('.choice-btn');
        buttons.forEach(function(btn) {
            if (!btn.classList.contains('correct') && !btn.classList.contains('incorrect')) {
                btn.disabled = true;
                btn.classList.add('disabled-btn');
            }
        });

        api.enableNextButton();
    };

    // -- Visual effects --

    api.createConfetti = function(element) {
        var rect = element.getBoundingClientRect();
        var centerX = rect.left + rect.width / 2;
        var centerY = rect.top + rect.height / 2;
        _spawnParticles(centerX, centerY, 30, 100, 1000);
    };

    api.shakeElement = function(element) {
        if (!element) return;
        element.classList.add('shake');
        setTimeout(function() {
            element.classList.remove('shake');
        }, 500);
    };

    // -- Stats toggle --

    api.toggleStats = function() {
        var statsBanner = document.getElementById('stats-banner');
        var toggleButton = document.querySelector('.toggle-stats-btn');

        if (!statsBanner) return;

        if (_state.pageJustLoaded) {
            _state.pageJustLoaded = false;
            statsBanner.style.display = 'none';
            if (toggleButton) {
                toggleButton.textContent = 'Afficher les statistiques';
            }
            return;
        }

        if (statsBanner.style.display === 'block') {
            statsBanner.style.display = 'none';
            if (toggleButton) {
                toggleButton.textContent = 'Afficher les statistiques';
            }
        } else {
            statsBanner.style.display = 'block';
            if (toggleButton) {
                toggleButton.textContent = 'Masquer les statistiques';
            }
        }
    };

    // -- State access --

    api.getState = function() {
        return {
            answersCount: _state.answersCount,
            correctAnswers: _state.correctAnswers,
            currentScore: _state.currentScore,
            maxScore: _state.maxScore,
            timerValue: _state.timerValue,
            totalQuestions: _state.totalQuestions
        };
    };

    // Allow external code to mutate specific state values (needed by templates)
    api.setState = function(key, value) {
        if (_state.hasOwnProperty(key)) {
            _state[key] = value;
        }
    };

    // Clear the game timer (for templates that manage their own timer logic)
    api.clearTimer = function() {
        clearInterval(_state.timerInterval);
    };

    return api;
})();
