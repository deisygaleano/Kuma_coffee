document.addEventListener("DOMContentLoaded", () => {
  const passwordInputs = document.querySelectorAll(".auth-form input[type='password']");

  passwordInputs.forEach((input) => {
    if (input.closest(".auth-password-wrap")) {
      return;
    }

    const wrapper = document.createElement("div");
    wrapper.className = "auth-password-wrap";

    input.parentNode.insertBefore(wrapper, input);
    wrapper.appendChild(input);

    const button = document.createElement("button");
    button.type = "button";
    button.className = "auth-password-toggle";
    button.setAttribute("aria-label", "Mostrar contrasena");
    button.setAttribute("title", "Mostrar contrasena");
    button.innerHTML = `
      <svg class="auth-password-toggle__icon auth-password-toggle__icon--show" viewBox="0 0 24 24" aria-hidden="true">
        <path d="M2.1 12s3.3-6 9.9-6 9.9 6 9.9 6-3.3 6-9.9 6-9.9-6-9.9-6Z"></path>
        <circle cx="12" cy="12" r="3"></circle>
      </svg>
      <svg class="auth-password-toggle__icon auth-password-toggle__icon--hide" viewBox="0 0 24 24" aria-hidden="true">
        <path d="m3 3 18 18"></path>
        <path d="M10.6 10.6A3 3 0 0 0 12 15a3 3 0 0 0 2.4-4.8"></path>
        <path d="M9.9 5.2A10.8 10.8 0 0 1 12 5c6.6 0 9.9 7 9.9 7a18.4 18.4 0 0 1-3.1 4.1"></path>
        <path d="M6.1 6.6A18 18 0 0 0 2.1 12s3.3 7 9.9 7c1.5 0 2.8-.3 4-.8"></path>
      </svg>
    `;

    button.addEventListener("click", () => {
      const isPassword = input.type === "password";
      input.type = isPassword ? "text" : "password";
      button.classList.toggle("is-visible", isPassword);
      button.setAttribute("aria-label", isPassword ? "Ocultar contrasena" : "Mostrar contrasena");
      button.setAttribute("title", isPassword ? "Ocultar contrasena" : "Mostrar contrasena");
    });

    wrapper.appendChild(button);
  });
});
