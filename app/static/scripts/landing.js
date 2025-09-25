(function () {
  window.addEventListener('DOMContentLoaded', () => {
    const form = document.querySelector('[data-demo-form]');
    if (!form) return;
    const submitButton = form.querySelector('button[type="submit"]');

    form.addEventListener('submit', (event) => {
      event.preventDefault();
      if (submitButton) {
        submitButton.disabled = true;
        submitButton.textContent = 'Request sent';
      }
      form.reset();
    });
  });
})();
