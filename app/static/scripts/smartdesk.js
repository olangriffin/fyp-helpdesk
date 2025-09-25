(function () {
  const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');

  function initFadeIn() {
    const nodes = document.querySelectorAll('[data-animate="fade"]');
    if (!nodes.length || prefersReducedMotion.matches) {
      nodes.forEach((node) => node.classList.add('is-visible'));
      return;
    }

    const observer = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add('is-visible');
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.18, rootMargin: '0px 0px -40px 0px' });

    nodes.forEach((node) => {
      node.classList.add('fade-in');
      observer.observe(node);
    });
  }

  function initHoverTilt() {
    const tiltNodes = document.querySelectorAll('[data-hover-tilt="true"]');
    if (!tiltNodes.length) return;

    tiltNodes.forEach((node) => {
      node.addEventListener('pointermove', (event) => {
        const rect = node.getBoundingClientRect();
        const relX = (event.clientX - rect.left) / rect.width;
        const relY = (event.clientY - rect.top) / rect.height;
        const tiltX = ((relY - 0.5) * 8).toFixed(2);
        const tiltY = ((0.5 - relX) * 8).toFixed(2);
        node.style.setProperty('--tilt-x', `${tiltX}deg`);
        node.style.setProperty('--tilt-y', `${tiltY}deg`);
      });

      node.addEventListener('pointerleave', () => {
        node.style.setProperty('--tilt-x', '0deg');
        node.style.setProperty('--tilt-y', '0deg');
      });
    });
  }

  function initLogoutButtons() {
    document.querySelectorAll('[data-logout], [data-action="logout"]').forEach((button) => {
      button.addEventListener('click', async () => {
        button.disabled = true;
        button.textContent = 'Leaving…';
        try {
          const response = await fetch('/logout', {
            method: 'POST',
            credentials: 'same-origin',
          });
          if (response.ok) {
            window.location.href = '/';
            return;
          }
        } catch (error) {
          console.error(error);
        }
        button.disabled = false;
        button.textContent = 'Log out';
        window.alert('Unable to log out right now. Please try again.');
      });
    });
  }

  window.addEventListener('DOMContentLoaded', () => {
    initFadeIn();
    initHoverTilt();
    initLogoutButtons();
  });
})();
