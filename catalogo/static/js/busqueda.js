(function () {
      const input = document.querySelector('.catalogo-busqueda-input');
      if (!input) return;

      let timer = null;
      const DELAY = 400;
      const MIN_CHARS = 3;

      input.addEventListener('input', function () {
        clearTimeout(timer);
        const val = this.value.trim();

        if (val.length === 0 || val.length >= MIN_CHARS) {
          timer = setTimeout(function () {
            input.closest('form').submit();
          }, DELAY);
        }
      });
    })();