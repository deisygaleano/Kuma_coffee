    /* ── Hero slider (proceso del café) ── */
    (function () {
      const pista = document.getElementById('heroSliderPista');
      if (!pista) return;
      const puntos = document.querySelectorAll('.hero-slider__punto');
      const total = pista.querySelectorAll('.hero-slider__item').length;
      let actual = 0;
      let timer = null;

      function irA(idx) {
        actual = (idx + total) % total;
        pista.style.transform = 'translateX(-' + (actual * 100) + '%)';
        puntos.forEach((p, i) => p.classList.toggle('hero-slider__punto--activo', i === actual));
      }

      puntos.forEach(function (p) {
        p.addEventListener('click', function () {
          clearInterval(timer);
          irA(parseInt(this.dataset.hidx));
          timer = setInterval(function () { irA(actual + 1); }, 3500);
        });
      });

      timer = setInterval(function () { irA(actual + 1); }, 3500);

      /* Swipe táctil */
      let tx = null;
      pista.addEventListener('touchstart', function (e) { tx = e.touches[0].clientX; }, { passive: true });
      pista.addEventListener('touchend', function (e) {
        if (tx === null) return;
        const d = tx - e.changedTouches[0].clientX;
        if (Math.abs(d) > 40) { clearInterval(timer); irA(d > 0 ? actual + 1 : actual - 1); timer = setInterval(function () { irA(actual + 1); }, 3500); }
        tx = null;
      }, { passive: true });
    })();

    /* ── Slider productos destacados (3 por página en desktop, 1 en móvil) ── */
    (function () {
      const pista = document.getElementById('sliderPista');
      if (!pista) return;

      const items  = Array.from(pista.querySelectorAll('.slider-item'));
      const puntos = Array.from(document.querySelectorAll('.slider-punto'));
      const total  = items.length;
      let pagina   = 0;
      let autoTimer = null;

      /* Cuántos productos se muestran por página */
      function pp() { return window.innerWidth <= 700 ? 1 : 3; }

      /* Total de páginas */
      function totalPags() { return Math.ceil(total / pp()); }

      function irA(p) {
        const porPag = pp();
        const nPags  = totalPags();
        pagina = ((p % nPags) + nPags) % nPags;

        /* Ancho de cada item según cantidad por página */
        items.forEach(function (item) {
          item.style.flexBasis = (100 / porPag) + '%';
        });

        /* Desplazamiento: primer item de la página × ancho de cada item */
        const primerItem = pagina * porPag;
        pista.style.transform = 'translateX(-' + (primerItem * (100 / porPag)) + '%)';

        /* Puntos: uno por página, ocultar sobrantes */
        puntos.forEach(function (pt, i) {
          pt.classList.toggle('slider-punto--activo', i === pagina);
          pt.style.display = i < nPags ? '' : 'none';
        });

        /* Tarjeta central destacada (página de 3) */
        items.forEach(function (item, i) {
          const esCentro = porPag === 3 && i === primerItem + 1 && i < total;
          item.classList.toggle('slider-item--centro', esCentro);
        });
      }

      function reiniciarAuto() {
        clearInterval(autoTimer);
        autoTimer = setInterval(function () { irA(pagina + 1); }, 4000);
      }

      /* Controles prev / next */
      document.querySelector('.slider-btn--prev').addEventListener('click', function () {
        reiniciarAuto(); irA(pagina - 1);
      });
      document.querySelector('.slider-btn--next').addEventListener('click', function () {
        reiniciarAuto(); irA(pagina + 1);
      });

      /* Clic en punto */
      puntos.forEach(function (pt) {
        pt.addEventListener('click', function () {
          reiniciarAuto(); irA(parseInt(this.dataset.idx));
        });
      });

      /* Swipe táctil */
      let touchX = null;
      pista.addEventListener('touchstart', function (e) { touchX = e.touches[0].clientX; }, { passive: true });
      pista.addEventListener('touchend', function (e) {
        if (touchX === null) return;
        const diff = touchX - e.changedTouches[0].clientX;
        if (Math.abs(diff) > 40) { reiniciarAuto(); irA(diff > 0 ? pagina + 1 : pagina - 1); }
        touchX = null;
      }, { passive: true });

      /* Recalcular al redimensionar */
      window.addEventListener('resize', function () { irA(0); });

      irA(0);
      if (total > 1) reiniciarAuto();
    })();
