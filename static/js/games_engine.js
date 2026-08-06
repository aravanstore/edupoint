/* ============================================================
   Edu Point — Multi-game Engine v4 (ADVANCED MULTIPLAYER & REVIEW)
   - Dynamic Language Selector: 🇰🇷 🇬🇧 🇩🇪 🇨🇳 🇷🇺
   - Detailed Round History & Error Breakdown Table ("Как ответил vs Как нужно было отвечать")
   - Real Multiplayer Lobby & Room Scoreboard
   ============================================================ */

class EduPointGameEngine {
  constructor(config) {
    this.gameSlug = config.gameSlug;
    this.roomNumber = config.roomNumber || 1;
    this.playerName = config.playerName || 'Игрок';
    this.isHost = config.isHost || false;
    this.maxRounds = config.maxRounds || 10;
    this.roundTimeSec = config.roundTimeSec || 20;
    this.maxPlayers = config.maxPlayers || 4;
    this.difficulty = config.difficulty || 'easy';
    this.targetLanguage = config.targetLanguage || 'korean';
    this.csrfToken = config.csrfToken || '';

    this.currentRound = 0;
    this.score = 0;
    this.correctAnswers = 0;
    this.timer = null;
    this.timeLeft = 0;
    this.isGameActive = false;
    this.lobbyPollTimer = null;

    // Detailed History for Error Breakdown Table
    this.roundHistory = [];
    this.playersList = [];

    this.initDatasets();
    this.startLobbyPolling();
  }

  initDatasets() {
    this.wordBank = [
      // Easy / Beginner (A1-A2)
      {
        korean: '안녕하세요',
        english: 'Hello',
        german: 'Hallo',
        chinese: '你好 (Nǐ hǎo)',
        russian: 'Здравствуйте / Привет',
        hint: 'Приветствие при встрече людей',
        level: 'easy'
      },
      {
        korean: '감사합니다',
        english: 'Thank you',
        german: 'Danke',
        chinese: '谢谢 (Xièxie)',
        russian: 'Спасибо / Благодарю',
        hint: 'Выражение вежливой благодарности',
        level: 'easy'
      },
      {
        korean: '학교',
        english: 'School',
        german: 'Schule',
        chinese: '学校 (Xuéxiào)',
        russian: 'Школа / Заведение',
        hint: 'Место, где учатся студенты и ученики',
        level: 'easy'
      },
      {
        korean: '선생님',
        english: 'Teacher',
        german: 'Lehrer',
        chinese: '老师 (Lǎoshī)',
        russian: 'Учитель / Наставник',
        hint: 'Человек, обучающий предмету',
        level: 'easy'
      },
      {
        korean: '학생',
        english: 'Student',
        german: 'Schüler',
        chinese: '学生 (Xuéshēng)',
        russian: 'Студент / Ученик',
        hint: 'Учащийся в Академии знаний',
        level: 'easy'
      },
      {
        korean: '친구',
        english: 'Friend',
        german: 'Freund',
        chinese: '朋友 (Péngyǒu)',
        russian: 'Друг / Товарищ',
        hint: 'Близкий и надёжный человек',
        level: 'easy'
      },
      {
        korean: '사랑',
        english: 'Love',
        german: 'Liebe',
        chinese: '爱 (Ài)',
        russian: 'Любовь',
        hint: 'Глубокое искреннее чувство',
        level: 'easy'
      },
      {
        korean: '음식',
        english: 'Food',
        german: 'Essen',
        chinese: '食物 (Shíwù)',
        russian: 'Еда / Блюдо',
        hint: 'Вкусные продукты и блюда',
        level: 'easy'
      },
      {
        korean: '물',
        english: 'Water',
        german: 'Wasser',
        chinese: '水 (Shuǐ)',
        russian: 'Вода',
        hint: 'Жидкость для утоления жажды',
        level: 'easy'
      },
      {
        korean: '책',
        english: 'Book',
        german: 'Buch',
        chinese: '书 (Shū)',
        russian: 'Книга',
        hint: 'Источник бумажных знаний',
        level: 'easy'
      },

      // Medium / Intermediate (B1-B2)
      {
        korean: '공부하다',
        english: 'To study',
        german: 'Lernen',
        chinese: '学习 (Xuéxí)',
        russian: 'Учиться / Изучать',
        hint: 'Процесс освоения новых предметов',
        level: 'medium'
      },
      {
        korean: '행복하다',
        english: 'Happy',
        german: 'Glücklich',
        chinese: '幸福 (Xìngfú)',
        russian: 'Счастливый / Радостный',
        hint: 'Чувство полного благополучия',
        level: 'medium'
      },
      {
        korean: '아름답다',
        english: 'Beautiful',
        german: 'Schön',
        chinese: '美丽 (Měilì)',
        russian: 'Красивый / Прекрасный',
        hint: 'Эстетичный внешний вид',
        level: 'medium'
      },

      // Hard / Advanced (C1-C2)
      {
        korean: '성공',
        english: 'Success',
        german: 'Erfolg',
        chinese: '成功 (Chénggōng)',
        russian: 'Успех / Достижение',
        hint: 'Результативный итог упорного труда',
        level: 'hard'
      },
      {
        korean: '미래',
        english: 'Future',
        german: 'Zukunft',
        chinese: '未来 (Wèilái)',
        russian: 'Будущее',
        hint: 'Предстоящее время и перспективы',
        level: 'hard'
      }
    ];

    this.grammarBank = [
      { text: '저는 학교[ ? ] 가요.', options: ['에', '에서', '을', '를'], correct: 0, exp: 'Частица 에 указывает направление движения (куда).' },
      { text: 'She [ ? ] to school every day.', options: ['go', 'goes', 'going', 'gone'], correct: 1, exp: '3-е лицо единственного числа (She) требует окончание -es.' },
      { text: 'Ich [ ? ] Deutsch lernen.', options: ['will', 'wollt', 'wollen', 'wollte'], correct: 0, exp: 'Глагол wollen с местоимением Ich имеет форму will.' },
      { text: '你好！我是[ ? ]人。(Я из Кыргызстана)', options: ['吉尔吉斯斯坦', '韩国', '美国', '中国'], correct: 0, exp: '吉尔吉斯斯坦 означает Кыргызстан на китайском языке.' }
    ];
  }

  setTargetLanguage(lang) {
    this.targetLanguage = lang;
    this.showFeedback(true, `Язык игры изменён: ${this.getLanguageLabel(lang)}`);
  }

  getLanguageLabel(lang) {
    switch (lang) {
      case 'korean': return '🇰🇷 Корейский';
      case 'english': return '🇬🇧 Английский';
      case 'german': return '🇩🇪 Немецкий';
      case 'chinese': return '🇨🇳 Китайский';
      case 'russian': return '🇷🇺 Русский';
      default: return '🌐 Все языки';
    }
  }

  getWordForLanguage(item) {
    switch (this.targetLanguage) {
      case 'english': return { targetWord: item.english, sourcePrompt: item.russian, langLabel: '🇬🇧 Английский' };
      case 'german': return { targetWord: item.german, sourcePrompt: item.russian, langLabel: '🇩🇪 Немецкий' };
      case 'chinese': return { targetWord: item.chinese, sourcePrompt: item.russian, langLabel: '🇨🇳 Китайский' };
      case 'russian': return { targetWord: item.russian, sourcePrompt: item.english, langLabel: '🇷🇺 Русский' };
      case 'korean':
      default:
        return { targetWord: item.korean, sourcePrompt: item.russian, langLabel: '🇰🇷 Корейский' };
    }
  }

  startLobbyPolling() {
    this.fetchRoomStatus();
    this.lobbyPollTimer = setInterval(() => {
      if (!this.isGameActive) {
        this.fetchRoomStatus();
      }
    }, 2000);
  }

  fetchRoomStatus() {
    fetch(`/games/${this.gameSlug}/room/${this.roomNumber}/status/`)
      .then(res => res.json())
      .then(data => {
        if (data.players) {
          this.playersList = data.players;
          this.isHost = data.is_host;
          this.maxPlayers = data.max_players;
          this.renderLobby();
        }

        if (data.status === 'in_game' && !this.isGameActive) {
          clearInterval(this.lobbyPollTimer);
          this.startGame();
        }
      })
      .catch(err => console.error('Lobby status fetch error:', err));
  }

  renderLobby() {
    const box = document.getElementById('lobbyPlayersBox');
    if (!box) return;

    box.innerHTML = `
      <div class="d-flex justify-content-between align-items-center mb-3">
        <h5 class="fw-bold mb-0">Реальные Участники комнаты (<span class="text-primary">${this.playersList.length}/${this.maxPlayers}</span>):</h5>
        <span class="badge bg-success"><span class="pulse-dot"></span>Онлайн Лобби</span>
      </div>

      <div class="lobby-player-grid">
        ${this.playersList.map((p) => `
          <div class="player-slot-card occupied ${p.is_host ? 'host-slot' : ''} animate__animated animate__zoomIn">
            <div class="player-avatar-circle">
              ${p.avatar || '😎'}
              ${p.is_host ? '<span class="host-badge-icon">👑</span>' : ''}
            </div>
            <strong class="d-block text-truncate" style="font-size:0.95rem;">${p.name}</strong>
            <span class="ready-pill ${p.is_ready ? '' : 'waiting'}">
              ${p.is_host ? '👑 Хост' : (p.is_ready ? '✅ В сети' : '⏳ Ждёт')}
            </span>
          </div>
        `).join('')}

        ${Array.from({ length: Math.max(0, this.maxPlayers - this.playersList.length) }).map(() => `
          <div class="player-slot-card opacity-50">
            <div class="player-avatar-circle text-muted">➕</div>
            <small class="text-muted">Свободный слот</small>
          </div>
        `).join('')}
      </div>
    `;

    const hostControls = document.getElementById('hostControlsBox');
    if (hostControls) {
      const isSoloOrHost = this.isHost || this.playersList.length <= 1 || this.playersList.some(p => p.name === this.playerName && p.is_host);
      if (isSoloOrHost) {
        hostControls.innerHTML = `
          <div class="alert alert-warning border-0 rounded-4 text-center mb-3 shadow-sm">
            👑 <strong>Вы — Хост комнаты!</strong> Вы можете запустить игру досрочно прямо сейчас.
          </div>
          <button class="btn-host-start w-100 justify-content-center" onclick="window.gameEngine.triggerHostStart()">
            🚀 НАЧАТЬ ИГРУ (ДОСРОЧНО)
          </button>
        `;
      } else {
        hostControls.innerHTML = `
          <div class="alert alert-info border-0 rounded-4 text-center mb-3">
            ⏳ Ожидаем команды от Хоста <strong>${this.playersList.find(p=>p.is_host)?.name || 'Хоста'}</strong> для запуска матча...
          </div>
          <button class="btn btn-outline-primary w-100 rounded-pill py-2" onclick="window.gameEngine.triggerHostStart()">
            🚀 Начать игру без ожидания
          </button>
        `;
      }
    }
  }

  triggerHostStart() {
    fetch(`/games/${this.gameSlug}/room/${this.roomNumber}/start/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': this.csrfToken
      }
    })
    .then(res => res.json())
    .then(data => {
      if (data.success) {
        this.startGame();
      }
    })
    .catch(err => console.error('Error starting game:', err));
  }

  startGame() {
    clearInterval(this.lobbyPollTimer);
    this.currentRound = 0;
    this.score = 0;
    this.correctAnswers = 0;
    this.roundHistory = [];
    this.isGameActive = true;

    document.getElementById('welcomeScreen')?.classList.add('d-none');
    document.getElementById('arenaScreen')?.classList.remove('d-none');
    document.getElementById('resultsScreen')?.classList.add('d-none');

    this.nextRound();
  }

  nextRound() {
    if (this.currentRound >= this.maxRounds) {
      this.endGame();
      return;
    }

    this.currentRound++;
    this.updateDashboard();
    this.startTimer(this.roundTimeSec);

    switch (this.gameSlug) {
      case 'mafia':
        this.renderMafiaRound();
        break;
      case 'wordle':
        this.renderWordleRound();
        break;
      case 'scramble':
        this.renderScrambleRound();
        break;
      case 'speed-typing':
        this.renderSpeedTypingRound();
        break;
      case 'memory-match':
        this.renderMemoryRound();
        break;
      case 'grammar-battle':
        this.renderGrammarRound();
        break;
      case 'sound-master':
        this.renderSoundRound();
        break;
      case 'context-quiz':
        this.renderContextRound();
        break;
      case 'academic-duel':
        this.renderAcademicRound();
        break;
      case 'quiz-master':
      default:
        this.renderQuizRound();
        break;
    }
  }

  startTimer(seconds) {
    clearInterval(this.timer);
    this.timeLeft = seconds;
    this.updateTimerDisplay();

    this.timer = setInterval(() => {
      this.timeLeft--;
      this.updateTimerDisplay();
      if (this.timeLeft <= 5 && this.timeLeft > 0) {
        if (window.gameAudio) window.gameAudio.playCountdown();
      }

      if (this.timeLeft <= 0) {
        clearInterval(this.timer);
        this.handleTimeout();
      }
    }, 1000);
  }

  updateTimerDisplay() {
    const el = document.getElementById('gameTimerText');
    const bar = document.getElementById('gameProgressBar');
    if (el) el.innerText = `${this.timeLeft}s`;
    if (bar) {
      const pct = (this.timeLeft / this.roundTimeSec) * 100;
      bar.style.width = `${pct}%`;
    }
  }

  updateDashboard() {
    const roundEl = document.getElementById('roundCounterText');
    const scoreEl = document.getElementById('scoreCounterText');
    if (roundEl) roundEl.innerText = `${this.currentRound} / ${this.maxRounds}`;
    if (scoreEl) scoreEl.innerText = `${this.score} pts`;
  }

  handleTimeout() {
    if (window.gameAudio) window.gameAudio.playWrong();
    this.logRoundHistory('Время вышло', false);
    this.showFeedback(false, 'Время вышло!');
    setTimeout(() => this.nextRound(), 1400);
  }

  registerAnswer(isCorrect, points = 100, userAnswerStr = '', correctAnswerStr = '') {
    clearInterval(this.timer);
    this.logRoundHistory(userAnswerStr, isCorrect, correctAnswerStr);

    if (isCorrect) {
      this.score += points + (this.timeLeft * 5);
      this.correctAnswers++;
      if (window.gameAudio) window.gameAudio.playCorrect();
      this.showFeedback(true, `+${points} Отлично!`);
    } else {
      if (window.gameAudio) window.gameAudio.playWrong();
      this.showFeedback(false, 'Неверно!');
    }
    this.updateDashboard();
    setTimeout(() => this.nextRound(), 1400);
  }

  logRoundHistory(userAnswer, isCorrect, customCorrectAnswer = '') {
    const questionText = this.currentQuestionText || 'Вопрос';
    const correctVal = customCorrectAnswer || this.currentCorrectAnswer || 'Правильный ответ';

    this.roundHistory.push({
      round: this.currentRound,
      question: questionText,
      userAnswer: userAnswer || (isCorrect ? correctVal : 'Неверный вариант'),
      correctAnswer: correctVal,
      isCorrect: isCorrect
    });
  }

  showFeedback(isSuccess, message) {
    const box = document.getElementById('gameFeedbackBox');
    if (!box) return;
    box.className = `alert mt-3 ${isSuccess ? 'alert-success' : 'alert-danger'} text-center fw-bold fs-5 animate__animated animate__bounceIn`;
    box.innerText = message;
    box.classList.remove('d-none');
    setTimeout(() => box.classList.add('d-none'), 1300);
  }

  // --- MULTILINGUAL RENDER MODES ---

  renderQuizRound() {
    const item = this.wordBank[Math.floor(Math.random() * this.wordBank.length)];
    const langObj = this.getWordForLanguage(item);

    this.currentQuestionText = `${langObj.targetWord} (${langObj.langLabel})`;
    this.currentCorrectAnswer = item.russian;

    const wrong = this.wordBank.filter(w => w.russian !== item.russian).sort(() => 0.5 - Math.random()).slice(0, 3);
    const options = [item, ...wrong].sort(() => 0.5 - Math.random());

    const arena = document.getElementById('gameArenaContent');
    arena.innerHTML = `
      <div class="text-center mb-4">
        <span class="badge bg-primary fs-6 mb-2">${langObj.langLabel} (${item.level.toUpperCase()})</span>
        <h2 class="display-4 fw-bold text-primary mb-2">${langObj.targetWord}</h2>
        <p class="fs-5 text-muted">Выберите верный перевод на русский язык:</p>
      </div>
      <div class="row g-3 justify-content-center">
        ${options.map((opt, i) => `
          <div class="col-md-6">
            <button class="quiz-option-btn" onclick="window.gameEngine.checkQuizAnswer(${opt.russian === item.russian}, '${opt.russian}')">
              <span>${i + 1}. <strong>${opt.russian}</strong></span>
              <i class="bi bi-chevron-right text-primary"></i>
            </button>
          </div>
        `).join('')}
      </div>
    `;
  }

  checkQuizAnswer(isCorrect, selectedAnswer) {
    this.registerAnswer(isCorrect, 100, selectedAnswer, this.currentCorrectAnswer);
  }

  renderMafiaRound() {
    const item = this.wordBank[Math.floor(Math.random() * this.wordBank.length)];
    const langObj = this.getWordForLanguage(item);
    const isPlayerMafia = Math.random() < 0.3;
    if (window.gameAudio && isPlayerMafia) window.gameAudio.playMafiaReveal();

    this.currentQuestionText = `Мафия: ${langObj.targetWord}`;
    this.currentCorrectAnswer = item.russian;

    const arena = document.getElementById('gameArenaContent');
    arena.innerHTML = `
      <div class="mafia-role-card mb-4">
        <span class="fs-1">${isPlayerMafia ? '🕵️‍♂️' : '🎓'}</span>
        <h3>Ваша роль: ${isPlayerMafia ? '<span class="text-danger">МАФИЯ</span>' : '<span class="text-info">ЗНАТОК</span>'}</h3>
        <p class="mb-0 text-white-50">${isPlayerMafia ? 'Запутайте участников, дав ложный перевод!' : 'Найдите подозрительного игрока с ложным мнением!'}</p>
      </div>
      <div class="card p-4 text-center">
        <h4>Слово раунда: <strong class="text-primary">${langObj.targetWord}</strong></h4>
        <p class="fs-5 text-muted">Истинный перевод: "${item.russian}"</p>
        <p class="fw-bold text-danger">Кто из игроков наговорил ложный вариант?</p>
        <div class="mafia-vote-grid">
          ${this.playersList.map((p, idx) => `
            <div class="mafia-player-box" onclick="window.gameEngine.voteMafia(${idx}, '${p.name}')">
              <span class="fs-3">${p.avatar || '👤'}</span>
              <div class="fw-bold">${p.name}</div>
            </div>
          `).join('')}
        </div>
      </div>
    `;
  }

  voteMafia(playerIdx, playerName) {
    const isCorrect = (playerIdx === 1 || playerIdx === 2);
    this.registerAnswer(isCorrect, 150, `Голос за ${playerName}`, 'Мафиози был разоблачён');
  }

/* Hangul Syllables Assembly Engine (Unicode 0xAC00 to 0xD7A3) */
class HangulComposer {
  static CHOSUNG = ['ㄱ', 'ㄲ', 'ㄴ', 'ㄷ', 'ㄸ', 'ㄹ', 'ㅁ', 'ㅂ', 'ㅃ', 'ㅅ', 'ㅆ', 'ㅇ', 'ㅈ', 'ㅉ', 'ㅊ', 'ㅋ', 'ㅌ', 'ㅍ', 'ㅎ'];
  static JUNGSUNG = ['ㅏ', 'ㅐ', 'ㅑ', 'ㅒ', 'ㅓ', 'ㅔ', 'ㅕ', 'ㅖ', 'ㅗ', 'ㅘ', 'ㅙ', 'ㅚ', 'ㅛ', 'ㅜ', 'ㅝ', 'ㅞ', 'ㅟ', 'ㅠ', 'ㅡ', 'ㅢ', 'ㅣ'];
  static JONGSUNG = ['', 'ㄱ', 'ㄲ', 'ㄳ', 'ㄴ', 'ㄵ', 'ㄶ', 'ㄷ', 'ㄹ', 'ㄺ', 'ㄻ', 'ㄼ', 'ㄽ', 'ㄾ', 'ㄿ', 'ㅀ', 'ㅁ', 'ㅂ', 'ㅄ', 'ㅅ', 'ㅆ', 'ㅇ', 'ㅈ', 'ㅊ', 'ㅋ', 'ㅌ', 'ㅍ', 'ㅎ'];

  static isConsonant(char) {
    return this.CHOSUNG.includes(char);
  }

  static isVowel(char) {
    return this.JUNGSUNG.includes(char);
  }

  static compose(cho, jung, jong = '') {
    const choIdx = this.CHOSUNG.indexOf(cho);
    const jungIdx = this.JUNGSUNG.indexOf(jung);
    const jongIdx = this.JONGSUNG.indexOf(jong);

    if (choIdx === -1 || jungIdx === -1) return cho + jung + (jong || '');

    const code = 0xAC00 + (choIdx * 588) + (jungIdx * 28) + (jongIdx > 0 ? jongIdx : 0);
    return String.fromCharCode(code);
  }

  static appendJamo(currentText, jamo) {
    if (!currentText) return jamo;

    const lastChar = currentText.slice(-1);
    const code = lastChar.charCodeAt(0);

    // If last char is isolated jamo consonant and current is vowel -> combine (e.g. ㄱ + ㅏ = 가)
    if (this.isConsonant(lastChar) && this.isVowel(jamo)) {
      const composed = this.compose(lastChar, jamo);
      return currentText.slice(0, -1) + composed;
    }

    // If last char is a composed Hangul syllable (0xAC00..0xD7A3)
    if (code >= 0xAC00 && code <= 0xD7A3) {
      const index = code - 0xAC00;
      const choIdx = Math.floor(index / 588);
      const jungIdx = Math.floor((index % 588) / 28);
      const jongIdx = index % 28;

      const cho = this.CHOSUNG[choIdx];
      const jung = this.JUNGSUNG[jungIdx];

      // Add final consonant (Jongsung) if no final consonant exists yet (e.g. 가 + ㄴ = 간)
      if (jongIdx === 0 && this.isConsonant(jamo)) {
        const newJongIdx = this.JONGSUNG.indexOf(jamo);
        if (newJongIdx > 0) {
          const composed = this.compose(cho, jung, jamo);
          return currentText.slice(0, -1) + composed;
        }
      }

      // If final consonant exists and current is a vowel, split final consonant to start new syllable (e.g. 간 + ㅏ = 가나)
      if (jongIdx > 0 && this.isVowel(jamo)) {
        const jongChar = this.JONGSUNG[jongIdx];
        const prevSyllable = this.compose(cho, jung, '');
        const newSyllable = this.compose(jongChar, jamo, '');
        return currentText.slice(0, -1) + prevSyllable + newSyllable;
      }
    }

    return currentText + jamo;
  }
}

  renderVirtualKeyboard(inputId, onSubmitFunctionName) {
    let rows = [];
    let langTitle = 'Английский (QWERTY)';

    if (this.targetLanguage === 'korean') {
      langTitle = '🇰🇷 Корейская клавиатура (Dubeolsik 두벌식)';
      rows = [
        ['ㅂ', 'ㅈ', 'ㄷ', 'ㄱ', 'ㅅ', 'ㅛ', 'ㅕ', 'ㅑ', 'ㅐ', 'ㅔ'],
        ['ㅁ', 'ㄴ', 'ㅇ', 'ㄹ', 'ㅎ', 'ㅗ', 'ㅓ', 'ㅏ', 'ㅣ'],
        ['ㅋ', 'ㅌ', 'ㅍ', 'ㅊ', 'ㅠ', 'ㅜ', 'ㅡ', '⌫', '↵']
      ];
    } else if (this.targetLanguage === 'german') {
      langTitle = '🇩🇪 Немецкая клавиатура (QWERTZ)';
      rows = [
        ['Q', 'W', 'E', 'R', 'T', 'Z', 'U', 'I', 'O', 'P', 'Ü'],
        ['A', 'S', 'D', 'F', 'G', 'H', 'J', 'K', 'L', 'Ö', 'Ä'],
        ['Y', 'X', 'C', 'V', 'B', 'N', 'M', 'ß', '⌫', '↵']
      ];
    } else if (this.targetLanguage === 'russian') {
      langTitle = '🇷🇺 Русская клавиатура (ЙЦУКЕН)';
      rows = [
        ['Й', 'Ц', 'У', 'К', 'Е', 'Н', 'Г', 'Ш', 'Щ', 'З', 'Х'],
        ['Ф', 'Ы', 'В', 'А', 'П', 'Р', 'О', 'Л', 'Д', 'Ж', 'Э'],
        ['Я', 'Ч', 'С', 'М', 'И', 'Т', 'Ь', 'Б', 'Ю', '⌫', '↵']
      ];
    } else {
      langTitle = '🇬🇧 Английская клавиатура (QWERTY)';
      rows = [
        ['Q', 'W', 'E', 'R', 'T', 'Y', 'U', 'I', 'O', 'P'],
        ['A', 'S', 'D', 'F', 'G', 'H', 'J', 'K', 'L'],
        ['Z', 'X', 'C', 'V', 'B', 'N', 'M', '⌫', '↵']
      ];
    }

    return `
      <div class="virtual-keyboard animate__animated animate__fadeInUp">
        <div class="vk-header">
          <small class="fw-bold text-primary"><i class="bi bi-keyboard-fill me-1"></i> ${langTitle}</small>
          <small class="text-muted d-none d-md-inline">Интерактивный авто-сборщик Hangul (가, 한, 국)</small>
        </div>
        ${rows.map(row => `
          <div class="vk-row">
            ${row.map(key => {
              if (key === '⌫') {
                return `<button type="button" class="vk-key vk-key-wide vk-key-backspace" onclick="window.gameEngine.pressVkKey('${inputId}', 'BACKSPACE')">⌫ Сброс</button>`;
              }
              if (key === '↵') {
                return `<button type="button" class="vk-key vk-key-wide vk-key-enter" onclick="window.gameEngine.${onSubmitFunctionName}()">↵ Готово</button>`;
              }
              return `<button type="button" class="vk-key" onclick="window.gameEngine.pressVkKey('${inputId}', '${key}')">${key}</button>`;
            }).join('')}
          </div>
        `).join('')}
      </div>
    `;
  }

  pressVkKey(inputId, keyChar) {
    const input = document.getElementById(inputId);
    if (!input) return;
    if (window.gameAudio) window.gameAudio.playKeyPress();

    if (keyChar === 'BACKSPACE') {
      input.value = input.value.slice(0, -1);
    } else {
      if (this.targetLanguage === 'korean') {
        input.value = HangulComposer.appendJamo(input.value, keyChar);
      } else {
        input.value += keyChar;
      }
    }
    input.focus();
  }

  renderWordleRound() {
    const item = this.wordBank[Math.floor(Math.random() * this.wordBank.length)];
    this.currentQuestionText = `Отгадай слово: ${item.russian}`;
    this.currentCorrectAnswer = item.english.toUpperCase();
    const targetWord = item.english.toUpperCase();

    const arena = document.getElementById('gameArenaContent');
    arena.innerHTML = `
      <div class="text-center mb-4">
        <h3 class="fw-bold">Отгадай слово по подсказке:</h3>
        <p class="fs-5 text-primary">💡 Подсказка: <strong>"${item.russian}"</strong> (${item.hint})</p>
        <div class="tile-box my-3">
          ${targetWord.split('').map(() => `<div class="letter-tile">?</div>`).join('')}
        </div>
        <div class="col-md-7 mx-auto mt-3">
          <input type="text" id="wordleInput" class="form-control form-control-lg text-center text-uppercase fw-bold fs-3" placeholder="Введите слово" maxlength="${targetWord.length}">
          <button class="btn btn-primary-ep w-100 mt-2 fs-5" onclick="window.gameEngine.submitWordle()">Проверить слово</button>
        </div>
        ${this.renderVirtualKeyboard('wordleInput', 'submitWordle')}
      </div>
    `;
  }

  submitWordle() {
    const input = document.getElementById('wordleInput');
    if (!input) return;
    const val = input.value.trim().toUpperCase();
    const isCorrect = (val === this.currentCorrectAnswer);
    this.registerAnswer(isCorrect, 120, val, this.currentCorrectAnswer);
  }

  renderScrambleRound() {
    const item = this.wordBank[Math.floor(Math.random() * this.wordBank.length)];
    const original = item.english.toUpperCase();
    this.currentQuestionText = `Собери из букв: ${item.russian}`;
    this.currentCorrectAnswer = original;

    const scrambled = original.split('').sort(() => 0.5 - Math.random());
    this.userScramble = [];

    const arena = document.getElementById('gameArenaContent');
    arena.innerHTML = `
      <div class="text-center mb-4">
        <h3>Собери слово из букв:</h3>
        <p class="fs-5 text-primary">Перевод: <strong>${item.russian}</strong> — ${item.hint}</p>
        
        <div id="scrambleAnswerBox" class="tile-box border p-3 rounded-4 bg-light min-height-60">
          <span class="text-muted">Кликайте по буквам ниже...</span>
        </div>

        <div id="scrambleTilesBox" class="tile-box">
          ${scrambled.map((char, idx) => `
            <div class="letter-tile" data-idx="${idx}" onclick="window.gameEngine.clickScrambleTile(this, '${char}')">${char}</div>
          `).join('')}
        </div>

        <div class="mt-3">
          <button class="btn btn-outline-danger btn-sm me-2" onclick="window.gameEngine.renderScrambleRound()">🔄 Сброс</button>
          <button class="btn btn-primary-ep px-4" onclick="window.gameEngine.checkScramble()">Проверить</button>
        </div>
      </div>
    `;
  }

  clickScrambleTile(el, char) {
    if (el.classList.contains('used')) return;
    if (window.gameAudio) window.gameAudio.playClick();

    el.classList.add('used');
    this.userScramble.push(char);

    const ansBox = document.getElementById('scrambleAnswerBox');
    ansBox.innerHTML = this.userScramble.map(c => `<div class="letter-tile">${c}</div>`).join('');
  }

  checkScramble() {
    const userStr = this.userScramble.join('');
    const isCorrect = (userStr === this.currentCorrectAnswer);
    this.registerAnswer(isCorrect, 110, userStr, this.currentCorrectAnswer);
  }

  renderSpeedTypingRound() {
    const item = this.wordBank[Math.floor(Math.random() * this.wordBank.length)];
    const langObj = this.getWordForLanguage(item);
    this.currentQuestionText = `Скоростной набор: ${langObj.targetWord}`;
    this.currentCorrectAnswer = langObj.targetWord;

    const arena = document.getElementById('gameArenaContent');
    arena.innerHTML = `
      <div class="text-center mb-4">
        <span class="badge bg-warning text-dark mb-2">⚡ Скоростной набор (${langObj.langLabel})</span>
        <h1 class="display-3 fw-bold text-primary my-3">${langObj.targetWord}</h1>
        <p class="fs-5 text-muted">Введите это слово точно как на экране (Перевод: ${item.russian}):</p>
        
        <div class="col-md-7 mx-auto">
          <input type="text" id="speedTypingInput" class="form-control form-control-lg text-center fw-bold fs-3" placeholder="${langObj.targetWord}" autofocus onkeypress="if(event.key==='Enter') window.gameEngine.submitSpeedTyping()">
          <button class="btn btn-primary-ep w-100 mt-3 fs-5" onclick="window.gameEngine.submitSpeedTyping()">Отправить (Enter)</button>
        </div>
        ${this.renderVirtualKeyboard('speedTypingInput', 'submitSpeedTyping')}
      </div>
    `;
  }

  submitSpeedTyping() {
    const input = document.getElementById('speedTypingInput');
    if (!input) return;
    const userVal = input.value.trim();
    const isCorrect = (userVal.toLowerCase() === this.currentCorrectAnswer.toLowerCase());
    this.registerAnswer(isCorrect, 150, userVal, this.currentCorrectAnswer);
  }

  renderMemoryRound() {
    const selected = this.wordBank.sort(() => 0.5 - Math.random()).slice(0, 4);
    const cards = [];
    selected.forEach((item, idx) => {
      const langObj = this.getWordForLanguage(item);
      cards.push({ id: idx, text: langObj.targetWord, pairId: idx });
      cards.push({ id: idx, text: item.russian, pairId: idx });
    });
    cards.sort(() => 0.5 - Math.random());

    this.currentQuestionText = `Поиск парных карточек`;
    this.currentCorrectAnswer = 'Все 4 пары найдены';

    this.flippedCards = [];
    this.matchedPairs = 0;

    const arena = document.getElementById('gameArenaContent');
    arena.innerHTML = `
      <div class="text-center mb-3">
        <h3>Найдите совпадающие пары карточек:</h3>
        <p class="text-muted">Иностранное слово <i class="bi bi-arrow-left-right"></i> Русский перевод</p>
      </div>
      <div class="memory-grid">
        ${cards.map((c, i) => `
          <div class="memory-card" id="memCard_${i}" onclick="window.gameEngine.flipMemoryCard(${i}, ${c.pairId}, '${c.text}')">
            <span>❓</span>
          </div>
        `).join('')}
      </div>
    `;
  }

  flipMemoryCard(cardIdx, pairId, text) {
    if (this.flippedCards.length >= 2) return;
    const cardEl = document.getElementById(`memCard_${cardIdx}`);
    if (cardEl.classList.contains('flipped') || cardEl.classList.contains('matched')) return;

    if (window.gameAudio) window.gameAudio.playClick();
    cardEl.classList.add('flipped');
    cardEl.innerHTML = `<span>${text}</span>`;
    this.flippedCards.push({ idx: cardIdx, pairId: pairId, el: cardEl });

    if (this.flippedCards.length === 2) {
      const [first, second] = this.flippedCards;
      if (first.pairId === second.pairId) {
        if (window.gameAudio) window.gameAudio.playCorrect();
        first.el.classList.add('matched');
        second.el.classList.add('matched');
        this.matchedPairs++;
        this.score += 100;
        this.flippedCards = [];
        if (this.matchedPairs >= 4) {
          setTimeout(() => this.registerAnswer(true, 200, 'Совпали 4/4 пар', 'Все пары открыты'), 500);
        }
      } else {
        if (window.gameAudio) window.gameAudio.playWrong();
        setTimeout(() => {
          first.el.classList.remove('flipped');
          second.el.classList.remove('flipped');
          first.el.innerHTML = '<span>❓</span>';
          second.el.innerHTML = '<span>❓</span>';
          this.flippedCards = [];
        }, 900);
      }
    }
  }

  renderGrammarRound() {
    const item = this.grammarBank[Math.floor(Math.random() * this.grammarBank.length)];
    this.currentQuestionText = `Грамматика: ${item.text}`;
    this.currentCorrectAnswer = item.options[item.correct];

    const arena = document.getElementById('gameArenaContent');
    arena.innerHTML = `
      <div class="text-center mb-4">
        <span class="badge bg-info text-dark mb-2">🏛️ Грамматика</span>
        <h2 class="display-6 fw-bold text-primary my-3">${item.text}</h2>
        <p class="fs-5 text-muted">Выберите верный грамматический вариант для пропуска:</p>
      </div>
      <div class="row g-3 justify-content-center">
        ${item.options.map((opt, i) => `
          <div class="col-md-6">
            <button class="quiz-option-btn" onclick="window.gameEngine.checkQuizAnswer(${i === item.correct}, '${opt}')">
              <span>${i + 1}. <strong>${opt}</strong></span>
              <i class="bi bi-check-circle text-primary"></i>
            </button>
          </div>
        `).join('')}
      </div>
    `;
  }

  renderSoundRound() {
    const item = this.wordBank[Math.floor(Math.random() * this.wordBank.length)];
    this.currentQuestionText = `Аудирование: ${item.korean}`;
    this.currentCorrectAnswer = item.russian;

    const wrong = this.wordBank.filter(w => w.russian !== item.russian).sort(() => 0.5 - Math.random()).slice(0, 3);
    const options = [item, ...wrong].sort(() => 0.5 - Math.random());

    const arena = document.getElementById('gameArenaContent');
    arena.innerHTML = `
      <div class="text-center mb-4">
        <button class="btn btn-lg btn-primary-ep rounded-circle p-4 mb-3 shadow" onclick="window.gameEngine.speakWord('${item.korean}')">
          <i class="bi bi-volume-up-fill display-4"></i>
        </button>
        <h3>Нажмите для прослушивания звучания</h3>
        <p class="text-muted fs-5">Какое значение звучит в аудировании?</p>
      </div>
      <div class="row g-3 justify-content-center">
        ${options.map((opt, i) => `
          <div class="col-md-6">
            <button class="quiz-option-btn" onclick="window.gameEngine.checkQuizAnswer(${opt.russian === item.russian}, '${opt.russian}')">
              <span>${i + 1}. ${opt.russian} (${opt.hint})</span>
              <i class="bi bi-soundwave text-primary"></i>
            </button>
          </div>
        `).join('')}
      </div>
    `;
    this.speakWord(item.korean);
  }

  speakWord(text) {
    if ('speechSynthesis' in window) {
      const synth = window.speechSynthesis;
      const utter = new SpeechSynthesisUtterance(text);
      utter.lang = 'ko-KR';
      synth.speak(utter);
    }
  }

  renderContextRound() {
    this.renderGrammarRound();
  }

  renderAcademicRound() {
    this.renderQuizRound();
  }

  endGame() {
    this.isGameActive = false;
    clearInterval(this.timer);
    clearInterval(this.lobbyPollTimer);
    if (window.gameAudio) window.gameAudio.playWin();

    document.getElementById('arenaScreen')?.classList.add('d-none');
    document.getElementById('resultsScreen')?.classList.remove('d-none');

    document.getElementById('finalPlayerScore').innerText = this.score;
    document.getElementById('finalCorrectCount').innerText = `${this.correctAnswers} / ${this.maxRounds}`;

    // Render Detailed Review Table ("Как ответил vs Как нужно было отвечать")
    this.renderReviewTable();

    // Post score to Django API & automatically reset room status to free!
    fetch(`/games/api/${this.gameSlug}/save-result/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': this.csrfToken
      },
      body: JSON.stringify({
        player_name: this.playerName,
        score: this.score,
        correct_answers: this.correctAnswers,
        total_answers: this.maxRounds,
        room_number: this.roomNumber
      })
    })
    .then(res => res.json())
    .then(data => {
      if (data.podium) {
        this.renderPodium(data.podium);
      }
    })
    .catch(err => console.error('Error saving game result:', err));
  }

  renderReviewTable() {
    const box = document.getElementById('reviewTableBox');
    if (!box) return;

    box.innerHTML = `
      <div class="card p-4 rounded-4 shadow-sm border mt-4 text-start">
        <h4 class="fw-bold text-primary mb-3"><i class="bi bi-journal-check me-2"></i> Разбор ответов и работа над ошибками:</h4>
        <div class="table-responsive">
          <table class="table table-hover align-middle">
            <thead class="table-light">
              <tr>
                <th>#</th>
                <th>Задание / Вопрос</th>
                <th>Ваш ответ</th>
                <th>Правильный ответ</th>
                <th>Результат</th>
              </tr>
            </thead>
            <tbody>
              ${this.roundHistory.map(r => `
                <tr class="${r.isCorrect ? 'table-success-light' : 'table-danger-light'}">
                  <td><strong>${r.round}</strong></td>
                  <td><strong class="text-dark">${r.question}</strong></td>
                  <td>
                    <span class="${r.isCorrect ? 'text-success fw-bold' : 'text-danger fw-bold'}">
                      ${r.userAnswer}
                    </span>
                  </td>
                  <td><span class="text-primary fw-bold">${r.correctAnswer}</span></td>
                  <td>
                    ${r.isCorrect ? '<span class="badge bg-success">✅ Верно</span>' : '<span class="badge bg-danger">❌ Ошибка</span>'}
                  </td>
                </tr>
              `).join('')}
            </tbody>
          </table>
        </div>
      </div>
    `;
  }

  renderPodium(podium) {
    const box = document.getElementById('podiumBox');
    if (!box) return;

    box.innerHTML = `
      <div class="podium-container">
        <div class="podium-step podium-2">
          <span class="podium-avatar">🥈</span>
          <div>${podium[1] ? podium[1].name : 'Игрок #2'}</div>
          <small>${podium[1] ? podium[1].score : 0} pts</small>
        </div>
        <div class="podium-step podium-1">
          <span class="podium-avatar">👑 🥇</span>
          <div>${podium[0] ? podium[0].name : 'Чемпион'}</div>
          <small>${podium[0] ? podium[0].score : 0} pts</small>
        </div>
        <div class="podium-step podium-3">
          <span class="podium-avatar">🥉</span>
          <div>${podium[2] ? podium[2].name : 'Игрок #3'}</div>
          <small>${podium[2] ? podium[2].score : 0} pts</small>
        </div>
      </div>
    `;
  }
}

window.EduPointGameEngine = EduPointGameEngine;
