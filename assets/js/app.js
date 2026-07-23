/* Planta de Semillas Peletizadas — Interacciones */
(function () {
  'use strict';

  // Marca JS-ready inmediatamente (antes de DCL) para activar reveal-on-scroll.
  // El CSS usa .js-ready [data-reveal] por defecto = invisible; sin JS, todo es visible.
  document.documentElement.classList.add('js-on');
  if (document.body) document.body.classList.add('js-ready');
  document.addEventListener('DOMContentLoaded', () => {
    if (document.body) document.body.classList.add('js-ready');
  });

  document.addEventListener('DOMContentLoaded', () => {
    const path = window.location.pathname;
    const isFileProtocol = location.protocol === 'file:';
    const isEnglish = path.startsWith('/en') || path.endsWith('/en/') || /\/en\/[^/]+\.html$/.test(path);

    /* --- file:// path resolver ------------------------------------------------
       Si el sitio se abre con doble click (file://) los href absolutos del toggle
       y del brand no resuelven. Convertimos /algo → path relativo a la posición. */
    if (isFileProtocol) {
      const fileBase = decodeURIComponent(path.replace(/\/[^/]*$/, '')) || '';
      const fromDir = fileBase.replace(/^.*\//, '');
      document.querySelectorAll('a[href^="/"]').forEach((a) => {
        const abs = a.getAttribute('href');
        if (!abs || abs === '/' || abs.startsWith('//')) return;
        let target = abs.replace(/^\/+/, '');
        // Calcular relativización desde ubicación actual
        if (fromDir === target.split('/')[0] || target.startsWith(fromDir + '/')) {
          target = target.slice(fromDir.length + 1);
        } else if (target.startsWith('assets/')) {
          // Up-steps iguales a profundidad del path actual menos 1
          const depth = fileBase.split('/').filter(Boolean).length;
          target = '../'.repeat(depth) + target;
        } else {
          const depth = fileBase.split('/').filter(Boolean).length;
          target = '../'.repeat(depth) + target;
        }
        a.setAttribute('href', target);
      });
    }

    /* --- Lenguaje toggle active state ---------------------------------------- */
    const toggle = document.querySelector('.lang-toggle');
    if (toggle) {
      const es = toggle.querySelector('[data-lang="es"]');
      const en = toggle.querySelector('[data-lang="en"]');
      if (isEnglish && en) {
        en.classList.add('is-active');
        en.setAttribute('aria-current', 'true');
      }
      if (!isEnglish && es) {
        es.classList.add('is-active');
        es.setAttribute('aria-current', 'true');
      }
      if (es && !es.classList.contains('is-active')) es.removeAttribute('aria-current');
      if (en && !en.classList.contains('is-active')) en.removeAttribute('aria-current');
    }

    /* --- Skip link inyectado dinámicamente ----------------------------------- */
    if (!document.querySelector('.skip-link')) {
      const link = document.createElement('a');
      link.className = 'skip-link';
      link.href = '#main';
      link.textContent = 'Saltar al contenido principal · Skip to content';
      if (!document.querySelector('main').id) document.querySelector('main').id = 'main';
      document.body.insertBefore(link, document.body.firstChild);
    }

    /* --- Smooth scroll para anchors internos --------------------------------- */
    document.querySelectorAll('a[href^="#"]').forEach((a) => {
      a.addEventListener('click', (e) => {
        const id = a.getAttribute('href');
        if (id.length > 1) {
          const target = document.querySelector(id);
          if (target) {
            e.preventDefault();
            target.scrollIntoView({ behavior: 'smooth', block: 'start' });
          }
        }
      });
    });

    /* --- Reveal-on-scroll (con stagger limitado) ------------------------------ */
    if ('IntersectionObserver' in window && !matchMedia('(prefers-reduced-motion: reduce)').matches) {
      const io = new IntersectionObserver(
        (entries) => {
          entries.forEach((entry) => {
            if (entry.isIntersecting) {
              entry.target.classList.add('is-visible');
              io.unobserve(entry.target);
            }
          });
        },
        { rootMargin: '0px 0px -8% 0px', threshold: 0.04 }
      );
      document.querySelectorAll('[data-reveal]').forEach((el, idx) => {
        if (idx < 6) el.style.transitionDelay = idx * 60 + 'ms';
        io.observe(el);
      });
    } else {
      document.querySelectorAll('[data-reveal]').forEach((el) => el.classList.add('is-visible'));
    }

    /* --- Video frame placeholder --------------------------------------------- */
    const video = document.querySelector('.video-frame');
    if (video) {
      const hint = video.querySelector('.video-frame__hint');
      const triggerFlash = () => {
        video.classList.add('is-prompt');
        if (hint) {
          const original = hint.textContent;
          hint.textContent = 'Coloca assets/video/intro.mp4 y embebé un <video>';
          setTimeout(() => (hint.textContent = original), 4000);
        }
      };
      video.addEventListener('click', triggerFlash);
      video.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          triggerFlash();
        }
      });
    }
  });
})();
