(function () {
  function parseDataset(root, key, fallback) {
    try {
      const raw = root.dataset[key];
      return raw ? JSON.parse(raw) : fallback;
    } catch (error) {
      console.warn(`Unable to parse dataset for ${key}`, error);
      return fallback;
    }
  }

  function initHelpdeskForm() {
    const root = document.querySelector('[data-helpdesk-form-only]');
    if (!root) return;

    const form = root.querySelector('[data-helpdesk-form]');
    const issueSelect = form?.querySelector('[data-helpdesk-issue]');
    const formStatus = form?.querySelector('[data-form-status]');
    const dynamicSections = Array.from(root.querySelectorAll('.dynamic-field'));

    if (!form) {
      console.warn('Helpdesk form markup is missing.');
      return;
    }

    function resetDynamicSection(section) {
      section.querySelectorAll('[data-context-field]').forEach((field) => {
        if ('value' in field) {
          field.value = '';
        }
      });
    }

    function toggleDynamicFields(selectedIssue) {
      dynamicSections.forEach((section) => {
        const isActive = section.dataset.issue === selectedIssue;
        section.classList.toggle('is-active', isActive);
        if (!isActive) {
          resetDynamicSection(section);
        }
      });
    }

    issueSelect?.addEventListener('change', (event) => {
      toggleDynamicFields(event.target.value);
    });

    toggleDynamicFields(issueSelect?.value || '');

    form.addEventListener('submit', async (event) => {
      event.preventDefault();
      const formData = new FormData(form);
      const payload = Object.fromEntries(formData.entries());

      const contextLines = [];
      form.querySelectorAll('[data-context-field]').forEach((field) => {
        const value = field.value?.trim();
        if (value) {
          const labelNode = field.closest('.field')?.querySelector('label');
          const label = labelNode ? labelNode.textContent.replace(/:\s*$/, '') : field.name;
          contextLines.push(`${label}: ${value}`);
        }
        delete payload[field.name];
      });

      if (contextLines.length) {
        payload.additional_context = contextLines.join('\n');
      }

      if (formStatus) {
        formStatus.textContent = 'Submitting ticket…';
        formStatus.className = 'form-status';
      }

      try {
        const response = await fetch('/tickets', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        });
        const data = await response.json().catch(() => ({}));
        if (!response.ok) {
          throw new Error(data.detail || 'Submission failed');
        }
        form.reset();
        toggleDynamicFields('');
        if (formStatus) {
          formStatus.textContent = data.status === 'resolved'
            ? 'Ticket auto-resolved instantly. Review from your dashboard.'
            : 'Ticket created successfully.';
          formStatus.className = 'form-status success';
        }
      } catch (error) {
        console.error(error);
        if (formStatus) {
          formStatus.textContent = error instanceof Error ? error.message : 'Submission failed.';
          formStatus.className = 'form-status error';
        }
      }
    });
  }

  window.addEventListener('DOMContentLoaded', initHelpdeskForm);
})();
