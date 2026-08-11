/**
 * Edu Point — Main JavaScript
 * Sky Blue + White Theme
 */

/* ============================================================
   DARK MODE
   ============================================================ */
const DarkMode = {
  init() {
    const saved = localStorage.getItem('edupoint-theme') || 'light';
    this.apply(saved);
  },
  toggle() {
    const current = document.documentElement.getAttribute('data-theme') || 'light';
    const next = current === 'dark' ? 'light' : 'dark';
    this.apply(next);
    localStorage.setItem('edupoint-theme', next);
  },
  apply(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    const btn = document.getElementById('darkModeToggle');
    if (btn) {
      btn.innerHTML = theme === 'dark'
        ? '<svg width="18" height="18" fill="currentColor" viewBox="0 0 24 24"><path d="M12 2.25a.75.75 0 01.75.75v2.25a.75.75 0 01-1.5 0V3a.75.75 0 01.75-.75zM7.5 12a4.5 4.5 0 119 0 4.5 4.5 0 01-9 0zM18.894 6.166a.75.75 0 00-1.06-1.06l-1.591 1.59a.75.75 0 101.06 1.061l1.591-1.59zM21.75 12a.75.75 0 01-.75.75h-2.25a.75.75 0 010-1.5H21a.75.75 0 01.75.75zM17.834 18.894a.75.75 0 001.06-1.06l-1.59-1.591a.75.75 0 10-1.061 1.06l1.59 1.591zM12 18a.75.75 0 01.75.75V21a.75.75 0 01-1.5 0v-2.25A.75.75 0 0112 18zM7.758 17.303a.75.75 0 00-1.061-1.06l-1.591 1.59a.75.75 0 001.06 1.061l1.592-1.59zM6 12a.75.75 0 01-.75.75H3a.75.75 0 010-1.5h2.25A.75.75 0 016 12zM6.697 7.757a.75.75 0 001.06-1.06l-1.59-1.591a.75.75 0 00-1.061 1.06l1.59 1.591z"/></svg>'
        : '<svg width="18" height="18" fill="currentColor" viewBox="0 0 24 24"><path fill-rule="evenodd" d="M9.528 1.718a.75.75 0 01.162.819A8.97 8.97 0 009 6a9 9 0 009 9 8.97 8.97 0 003.463-.69.75.75 0 01.981.98 10.503 10.503 0 01-9.694 6.46c-5.799 0-10.5-4.701-10.5-10.5 0-4.368 2.667-8.112 6.46-9.694a.75.75 0 01.818.162z" clip-rule="evenodd"/></svg>';
    }
  }
};

/* ============================================================
   NAVBAR
   ============================================================ */
const Navbar = {
  init() {
    const navbar = document.querySelector('.navbar');
    if (!navbar) return;
    window.addEventListener('scroll', () => {
      navbar.classList.toggle('scrolled', window.scrollY > 50);
    });
    // Mobile menu close on link click
    document.querySelectorAll('.navbar-nav .nav-link').forEach(link => {
      link.addEventListener('click', () => {
        const collapse = document.getElementById('navbarNav');
        if (collapse && collapse.classList.contains('show')) {
          const bsCollapse = bootstrap.Collapse.getInstance(collapse);
          if (bsCollapse) bsCollapse.hide();
        }
      });
    });
    // Active link highlighting
    const currentPath = window.location.pathname;
    document.querySelectorAll('.navbar-nav .nav-link').forEach(link => {
      if (link.getAttribute('href') === currentPath ||
          (currentPath !== '/' && currentPath.startsWith(link.getAttribute('href') || ''))) {
        link.classList.add('active');
      }
    });
  }
};

/* ============================================================
   SCROLL TO TOP
   ============================================================ */
const ScrollTop = {
  init() {
    const btn = document.getElementById('scrollTopBtn');
    if (!btn) return;
    window.addEventListener('scroll', () => {
      btn.classList.toggle('visible', window.scrollY > 400);
    });
    btn.addEventListener('click', () => {
      window.scrollTo({ top: 0, behavior: 'smooth' });
    });
  }
};

/* ============================================================
   AOS — Scroll Animations
   ============================================================ */
const AnimateOnScroll = {
  init() {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('aos-animate');
          // Counter animation trigger
          const counter = entry.target.querySelector('.counter');
          if (counter) CounterAnimation.animate(counter);
        }
      });
    }, { threshold: 0.1, rootMargin: '0px 0px -60px 0px' });

    document.querySelectorAll('[data-aos]').forEach(el => observer.observe(el));
  }
};

/* ============================================================
   COUNTER ANIMATION
   ============================================================ */
const CounterAnimation = {
  animated: new Set(),
  animate(el) {
    if (this.animated.has(el)) return;
    this.animated.add(el);
    const target = parseInt(el.dataset.target || el.textContent.replace(/\D/g, '')) || 0;
    const suffix = el.dataset.suffix || '+';
    const duration = 1800;
    const start = performance.now();
    const update = (now) => {
      const elapsed = now - start;
      const progress = Math.min(elapsed / duration, 1);
      const ease = 1 - Math.pow(1 - progress, 3); // ease-out-cubic
      const current = Math.floor(ease * target);
      el.textContent = current.toLocaleString() + (progress < 1 ? '' : suffix);
      if (progress < 1) requestAnimationFrame(update);
    };
    requestAnimationFrame(update);
  },
  initAll() {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          this.animate(entry.target);
        }
      });
    }, { threshold: 0.5 });
    document.querySelectorAll('.counter').forEach(el => observer.observe(el));
  }
};

/* ============================================================
   AJAX SEARCH
   ============================================================ */
const Search = {
  timeout: null,
  init() {
    const input = document.getElementById('searchInput');
    const dropdown = document.getElementById('searchDropdown');
    if (!input || !dropdown) return;

    input.addEventListener('input', () => {
      clearTimeout(this.timeout);
      const q = input.value.trim();
      if (q.length < 2) {
        dropdown.classList.remove('show');
        return;
      }
      this.timeout = setTimeout(() => this.fetch(q, dropdown), 300);
    });

    document.addEventListener('click', (e) => {
      if (!input.contains(e.target) && !dropdown.contains(e.target)) {
        dropdown.classList.remove('show');
      }
    });

    input.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        window.location.href = `/search/?q=${encodeURIComponent(input.value)}`;
      }
    });
  },
  async fetch(q, dropdown) {
    try {
      const res = await fetch(`/search/?q=${encodeURIComponent(q)}`, {
        headers: { 'X-Requested-With': 'XMLHttpRequest' }
      });
      const data = await res.json();
      this.render(data, dropdown);
    } catch (e) {
      console.error('Search error:', e);
    }
  },
  render(data, dropdown) {
    const total = data.courses.length + data.news.length + data.teachers.length + data.exams.length;
    if (!total) {
      dropdown.innerHTML = '<div class="search-result-item text-muted">Ничего не найдено</div>';
      dropdown.classList.add('show');
      return;
    }
    let html = '';
    if (data.courses.length) {
      html += '<div class="search-result-item" style="font-weight:700;font-size:0.75rem;color:var(--text-muted);text-transform:uppercase;">Курсы</div>';
      data.courses.forEach(c => {
        html += `<div class="search-result-item" onclick="window.location='${c.url}'">
          <span style="color:var(--primary)">📚</span> ${c.name} <span style="color:var(--text-muted);font-size:0.8em">${c.category}</span>
        </div>`;
      });
    }
    if (data.teachers.length) {
      html += '<div class="search-result-item" style="font-weight:700;font-size:0.75rem;color:var(--text-muted);text-transform:uppercase;">Преподаватели</div>';
      data.teachers.forEach(t => {
        html += `<div class="search-result-item" onclick="window.location='${t.url}'">
          <span style="color:var(--primary)">👤</span> ${t.name} <span style="color:var(--text-muted);font-size:0.8em">${t.position}</span>
        </div>`;
      });
    }
    if (data.exams.length) {
      html += '<div class="search-result-item" style="font-weight:700;font-size:0.75rem;color:var(--text-muted);text-transform:uppercase;">Экзамены</div>';
      data.exams.forEach(e => {
        html += `<div class="search-result-item" onclick="window.location='${e.url}'">
          <span style="color:var(--primary)">🏆</span> ${e.name}
        </div>`;
      });
    }
    if (data.news.length) {
      html += '<div class="search-result-item" style="font-weight:700;font-size:0.75rem;color:var(--text-muted);text-transform:uppercase;">Новости</div>';
      data.news.forEach(n => {
        html += `<div class="search-result-item" onclick="window.location='${n.url}'">
          <span style="color:var(--primary)">📰</span> ${n.title}
        </div>`;
      });
    }
    dropdown.innerHTML = html;
    dropdown.classList.add('show');
  }
};

/* ============================================================
   GALLERY LIGHTBOX
   ============================================================ */
const Lightbox = {
  init() {
    const overlay = document.getElementById('lightboxOverlay');
    const img = document.getElementById('lightboxImg');
    if (!overlay || !img) return;

    document.querySelectorAll('.gallery-item').forEach(item => {
      item.addEventListener('click', () => {
        const src = item.querySelector('img')?.src;
        if (src) {
          img.src = src;
          overlay.classList.add('open');
          document.body.style.overflow = 'hidden';
        }
      });
    });

    overlay.addEventListener('click', (e) => {
      if (e.target === overlay || e.target.closest('.lightbox-close')) {
        overlay.classList.remove('open');
        document.body.style.overflow = '';
      }
    });

    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        overlay.classList.remove('open');
        document.body.style.overflow = '';
      }
    });
  }
};

/* ============================================================
   MESSAGES (Auto dismiss)
   ============================================================ */
const Messages = {
  init() {
    document.querySelectorAll('.alert-ep').forEach(alert => {
      setTimeout(() => {
        alert.style.opacity = '0';
        alert.style.transform = 'translateX(120%)';
        setTimeout(() => alert.remove(), 400);
      }, 5000);
    });
  }
};

/* ============================================================
   PRELOADER
   ============================================================ */
const Preloader = {
  init() {
    const preloader = document.getElementById('preloader');
    if (!preloader) return;
    window.addEventListener('load', () => {
      setTimeout(() => {
        preloader.classList.add('hidden');
        setTimeout(() => preloader.remove(), 500);
      }, 300);
    });
  }
};

/* ============================================================
   GALLERY FILTER
   ============================================================ */
const GalleryFilter = {
  init() {
    const filterBtns = document.querySelectorAll('[data-gallery-filter]');
    if (!filterBtns.length) return;
    filterBtns.forEach(btn => {
      btn.addEventListener('click', () => {
        const filter = btn.dataset.galleryFilter;
        filterBtns.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        document.querySelectorAll('.gallery-item').forEach(item => {
          const category = item.dataset.category;
          item.style.display = (filter === 'all' || category === filter) ? '' : 'none';
        });
      });
    });
  }
};

/* ============================================================
   FORM VALIDATION (Client side)
   ============================================================ */
const FormValidator = {
  init() {
    document.querySelectorAll('form[data-validate]').forEach(form => {
      form.addEventListener('submit', (e) => {
        let valid = true;
        form.querySelectorAll('[required]').forEach(field => {
          if (!field.value.trim()) {
            field.style.borderColor = 'var(--danger)';
            valid = false;
          } else {
            field.style.borderColor = '';
          }
          field.addEventListener('input', () => { field.style.borderColor = ''; }, { once: true });
        });
        if (!valid) {
          e.preventDefault();
          const firstInvalid = form.querySelector('[required]:invalid, [required][style*="danger"]');
          if (firstInvalid) firstInvalid.focus();
        }
      });
    });
  }
};

/* ============================================================
   PHONE INPUT FORMATTER
   ============================================================ */
const PhoneFormatter = {
  init() {
    document.querySelectorAll('input[type="tel"]').forEach(input => {
      input.addEventListener('input', () => {
        let val = input.value.replace(/\D/g, '');
        if (val.startsWith('996')) {
          val = '+' + val;
        } else if (val.startsWith('0')) {
          val = '+996' + val.slice(1);
        }
        input.value = val;
      });
    });
  }
};

/* ============================================================
   EASTER EGGS
   ============================================================ */
const EasterEggs = {
  init() {
    document.querySelectorAll('.easter-egg[data-egg-id]').forEach(el => {
      el.addEventListener('click', () => this.click(el));
    });
  },
  async click(el) {
    if (el.classList.contains('found')) return;
    const eggId = el.dataset.eggId;
    try {
      const res = await fetch(`/egg/${eggId}/`, {
        method: 'POST',
        headers: { 'X-Requested-With': 'XMLHttpRequest', 'X-CSRFToken': this.getCsrf() },
      });
      const data = await res.json();
      if (!data.ok) return;
      el.classList.add('found');
      this.updateCounter(data.count, data.total);
      if (data.is_new) this.showToast(data.count, data.total);
    } catch (e) {
      console.error('Egg error:', e);
    }
  },
  getCsrf() {
    const m = document.cookie.match(/csrftoken=([^;]+)/);
    return m ? m[1] : '';
  },
  updateCounter(count, total) {
    const counter = document.getElementById('eggCounter');
    if (!counter) return;
    counter.querySelector('.egg-counter-text').textContent = `${count}/${total}`;
    if (count >= total) counter.classList.add('egg-counter-complete');
  },
  showToast(count, total) {
    const toast = document.createElement('div');
    toast.className = 'egg-toast';
    toast.textContent = count >= total
      ? `🎉 Все пасхалки найдены! ${count}/${total}`
      : `🥚 Пасхалка найдена! ${count}/${total}`;
    document.body.appendChild(toast);
    requestAnimationFrame(() => toast.classList.add('show'));
    setTimeout(() => {
      toast.classList.remove('show');
      setTimeout(() => toast.remove(), 350);
    }, 2200);
  }
};

/* ============================================================
   INIT ALL
   ============================================================ */
document.addEventListener('DOMContentLoaded', () => {
  DarkMode.init();
  Navbar.init();
  ScrollTop.init();
  AnimateOnScroll.init();
  CounterAnimation.initAll();
  Search.init();
  Lightbox.init();
  Messages.init();
  Preloader.init();
  GalleryFilter.init();
  FormValidator.init();
  PhoneFormatter.init();
  EasterEggs.init();

  // Dark mode toggle button
  const toggleBtn = document.getElementById('darkModeToggle');
  if (toggleBtn) {
    toggleBtn.addEventListener('click', () => DarkMode.toggle());
  }
});
