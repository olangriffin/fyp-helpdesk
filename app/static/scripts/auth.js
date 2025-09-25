(function () {
  function displayMessage(messageEl, text, variant) {
    if (!messageEl) return;
    messageEl.textContent = text || '';
    messageEl.classList.remove('error', 'success', 'info');
    if (variant) {
      messageEl.classList.add(variant);
    }
  }

  async function submitForm(form, endpoint, successHandler) {
    const message = form.querySelector('.form-message');
    const submitButton = form.querySelector('button[type="submit"]');
    displayMessage(message, '', null);
    if (submitButton) submitButton.disabled = true;

    try {
      const formData = new FormData(form);
      const payload = {};
      for (const [key, rawValue] of formData.entries()) {
        const value = typeof rawValue === 'string' ? rawValue.trim() : rawValue;
        payload[key] = value === '' ? null : value;
      }

      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'same-origin',
        body: JSON.stringify(payload),
      });

      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        const detail = Array.isArray(data.detail)
          ? data.detail.map((item) => item.msg || item).join(', ')
          : (data.detail || 'Unable to complete the request.');
        throw new Error(detail);
      }

      successHandler({ data, messageEl: message });
    } catch (error) {
      console.error(error);
      const text = error instanceof Error ? error.message : 'Unable to complete the request.';
      displayMessage(message, text, 'error');
    } finally {
      if (submitButton) submitButton.disabled = false;
    }
  }

  async function resendVerification(email) {
    const trimmed = email?.trim();
    if (!trimmed) {
      window.alert('Enter your email first so we know where to send the verification message.');
      return;
    }
    try {
      const response = await fetch('/resend-verification', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email: trimmed }),
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(data.detail || 'Unable to resend verification email.');
      }
      window.alert(data.message || 'Verification email sent.');
    } catch (error) {
      const text = error instanceof Error ? error.message : 'Unable to resend verification email.';
      window.alert(text);
    }
  }

  function init() {
    const body = document.body;
    const params = new URLSearchParams(window.location.search);
    const modeButtons = document.querySelectorAll('.mode-button');
    const panels = {
      login: document.querySelector('[data-panel="login"]'),
      signup: document.querySelector('[data-panel="signup"]'),
    };
    const forms = {
      login: document.querySelector('[data-form="login"]'),
      signup: document.querySelector('[data-form="signup"]'),
    };

    function setMode(next) {
      const mode = next === 'signup' ? 'signup' : 'login';
      body.dataset.mode = mode;
      modeButtons.forEach((button) => {
        button.classList.toggle('is-active', button.dataset.switch === mode);
      });
      Object.entries(panels).forEach(([key, panel]) => {
        panel?.classList.toggle('is-active', key === mode);
      });
      params.set('mode', mode);
      const query = params.toString();
      const newUrl = query ? `${window.location.pathname}?${query}` : window.location.pathname;
      window.history.replaceState(null, '', newUrl);
      const focusTarget = document.querySelector(mode === 'signup' ? '#signup-email' : '#login-email');
      focusTarget?.focus();
    }

    modeButtons.forEach((button) => {
      button.addEventListener('click', () => setMode(button.dataset.switch));
    });

    document.querySelectorAll('.switch-link').forEach((link) => {
      link.addEventListener('click', () => setMode(link.dataset.switch));
    });

    setMode(body.dataset.mode);

    document.querySelectorAll('.toggle-password').forEach((toggle) => {
      toggle.addEventListener('click', () => {
        const input = document.getElementById(toggle.dataset.target);
        if (!input) return;
        const isHidden = input.type === 'password';
        input.type = isHidden ? 'text' : 'password';
        toggle.textContent = isHidden ? 'Hide' : 'Show';
      });
    });

    forms.login?.addEventListener('submit', (event) => {
      event.preventDefault();
      submitForm(forms.login, '/login', ({ data, messageEl }) => {
        displayMessage(messageEl, 'Login successful. Redirecting...', 'success');
        if (data.redirect_url) {
          window.setTimeout(() => {
            window.location.href = data.redirect_url;
          }, 400);
        }
      });
    });

    forms.signup?.addEventListener('submit', (event) => {
      event.preventDefault();
      submitForm(forms.signup, '/signup', ({ data, messageEl }) => {
        const text = data.message || 'Account created. Verify your email to continue.';
        displayMessage(messageEl, text, 'info');
        if (data.redirect_url) {
          window.setTimeout(() => {
            window.location.href = data.redirect_url;
          }, 900);
        }
      });
    });

    document.querySelectorAll('[data-resend]').forEach((link) => {
      link.addEventListener('click', () => {
        const mode = body.dataset.mode;
        const field = mode === 'signup'
          ? document.getElementById('signup-email')
          : document.getElementById('login-email');
        resendVerification(field?.value);
      });
    });

    const googleButton = document.querySelector('[data-action="oauth-google"]');
    googleButton?.addEventListener('click', async () => {
      const response = await fetch('/google/start');
      if (response.status === 501) {
        const data = await response.json().catch(() => ({}));
        window.alert(data.detail || 'Google OAuth is not yet configured.');
        return;
      }
      if (response.ok) {
        const data = await response.json().catch(() => ({}));
        if (data.redirect_url) {
          window.location.href = data.redirect_url;
        }
      }
    });
  }

  window.addEventListener('DOMContentLoaded', init);
})();
