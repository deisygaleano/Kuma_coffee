(function () {
  const form = document.querySelector(".inv-filtros");
  if (!form) return;

  const input = form.querySelector('input[name="q"]');
  const select = form.querySelector('select[name="estado"]');
  const STORAGE_KEY = "inventario-busqueda-focus";
  const MIN_CHARS = 3;
  const DELAY = 400;
  let timer = null;

  function guardarFoco() {
    if (!input) return;
    sessionStorage.setItem(
      STORAGE_KEY,
      JSON.stringify({
        pos: input.selectionStart ?? input.value.length,
      })
    );
  }

  function restaurarFoco() {
    if (!input) return;
    const guardado = sessionStorage.getItem(STORAGE_KEY);
    if (!guardado) return;

    sessionStorage.removeItem(STORAGE_KEY);
    let pos = input.value.length;
    try {
      const data = JSON.parse(guardado);
      if (typeof data.pos === "number") {
        pos = Math.min(data.pos, input.value.length);
      }
    } catch (error) {
      pos = input.value.length;
    }

    input.focus({ preventScroll: true });
    input.setSelectionRange(pos, pos);
  }

  form.addEventListener("submit", guardarFoco);

  if (input) {
    input.addEventListener("input", function () {
      clearTimeout(timer);
      const valor = this.value.trim();

      if (valor.length === 0 || valor.length >= MIN_CHARS) {
        timer = setTimeout(function () {
          form.submit();
        }, DELAY);
      }
    });
  }

  if (select) {
    select.addEventListener("change", function () {
      form.submit();
    });
  }

  restaurarFoco();
})();
