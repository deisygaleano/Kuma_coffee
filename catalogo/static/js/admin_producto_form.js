document.addEventListener("DOMContentLoaded", function () {
  const inputFile = document.getElementById("id_imagen_file");
  const zone = document.getElementById("imgZone");
  const previewBox = document.getElementById("preview-container");
  const previewImg = document.getElementById("preview-img");
  const changeButton = document.querySelector("[data-cambiar-imagen]");

  if (!inputFile || !zone || !previewBox || !previewImg) return;

  function abrirSelector() {
    inputFile.click();
  }

  function mostrarPreview() {
    const file = inputFile.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = function (event) {
      previewImg.src = event.target.result;
      zone.style.display = "none";
      previewBox.style.display = "block";
    };
    reader.readAsDataURL(file);
  }

  zone.addEventListener("click", abrirSelector);
  if (changeButton) changeButton.addEventListener("click", abrirSelector);
  inputFile.addEventListener("change", mostrarPreview);

  zone.addEventListener("dragover", function (event) {
    event.preventDefault();
    zone.classList.add("is-dragover");
  });

  zone.addEventListener("dragleave", function () {
    zone.classList.remove("is-dragover");
  });

  zone.addEventListener("drop", function (event) {
    event.preventDefault();
    zone.classList.remove("is-dragover");
    if (event.dataTransfer.files.length) {
      inputFile.files = event.dataTransfer.files;
      mostrarPreview();
    }
  });
});
