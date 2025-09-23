(function () {
  const STATUS_LABELS = {
    open: 'Open',
    in_progress: 'In Progress',
    waiting_for_customer: 'Waiting on Customer',
    resolved: 'Resolved',
  };

  function labelStatus(value) {
    return STATUS_LABELS[value] || value;
  }

  function formatDate(isoString) {
    const date = new Date(isoString);
    return date.toLocaleString(undefined, {
      hour: '2-digit',
      minute: '2-digit',
      day: 'numeric',
      month: 'short',
    });
  }

  function parseDataset(root, key, fallback) {
    try {
      const raw = root.dataset[key];
      return raw ? JSON.parse(raw) : fallback;
    } catch (error) {
      console.warn(`Unable to parse dataset for ${key}`, error);
      return fallback;
    }
  }

  async function fetchTickets() {
    const response = await fetch('/tickets');
    if (!response.ok) {
      throw new Error('Unable to load tickets');
    }
    return response.json();
  }

  async function patchTicket(id, payload) {
    const response = await fetch(`/tickets/${id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!response.ok) {
      throw new Error('Unable to update ticket');
    }
  }

  function initHelpdesk() {
    const root = document.querySelector('[data-helpdesk-dashboard]');
    if (!root) return;

    const statuses = parseDataset(root, 'statuses', []);
    const priorities = parseDataset(root, 'priorities', []);

    const formSection = root.querySelector('[data-helpdesk-form]');
    const form = formSection?.querySelector('form');
    const issueSelect = form?.querySelector('[data-helpdesk-issue]');
    const formStatus = formSection?.querySelector('[data-form-status]');
    const boardColumns = root.querySelector('[data-board-columns]');
    const template = root.querySelector('[data-template="ticket-card"]');
    const dynamicSections = Array.from(root.querySelectorAll('.dynamic-field'));

    if (!form || !boardColumns || !template) {
      console.warn('Helpdesk template is missing required elements.');
      return;
    }

    const columnBodies = new Map();

    function renderColumnShells() {
      boardColumns.innerHTML = '';
      columnBodies.clear();

      statuses.forEach((status) => {
        const column = document.createElement('div');
        column.className = 'board-column';
        column.dataset.statusColumn = status;
        column.innerHTML = `
          <header>
            <span>${labelStatus(status)}</span>
            <span class="status-pill" data-count>0</span>
          </header>
          <div class="column-body"></div>
        `;
        const body = column.querySelector('.column-body');
        boardColumns.appendChild(column);
        columnBodies.set(status, body);
      });
    }

    function renderTickets(tickets) {
      columnBodies.forEach((container) => {
        container.innerHTML = '';
      });
      const counts = new Map(statuses.map((status) => [status, 0]));

      tickets.forEach((ticket) => {
        const column = columnBodies.get(ticket.status);
        if (!column) return;
        counts.set(ticket.status, (counts.get(ticket.status) || 0) + 1);

        const card = template.content.firstElementChild.cloneNode(true);
        card.dataset.ticketId = ticket.id;
        card.querySelector('[data-ticket-subject]').textContent = ticket.subject;
        card.querySelector('[data-ticket-created]').textContent = formatDate(ticket.created_at);
        card.querySelector('[data-ticket-description]').textContent = ticket.description;
        card.querySelector('[data-ticket-priority]').textContent = `Priority: ${ticket.priority.toUpperCase()}`;
        card.querySelector('[data-ticket-issue]').textContent = `Type: ${ticket.issue_type.replace(/_/g, ' ')}`;
        card.querySelector('[data-ticket-requester]').textContent = `Requester: ${ticket.requester}`;
        card.querySelector('[data-ticket-assignee]').textContent = ticket.assignee ? `Assignee: ${ticket.assignee}` : 'Unassigned';

        const resolution = card.querySelector('[data-ticket-resolution]');
        if (ticket.resolution_notes) {
          resolution.textContent = ticket.resolution_notes;
          resolution.hidden = false;
        } else {
          resolution.hidden = true;
        }

        const select = card.querySelector('[data-ticket-status]');
        select.innerHTML = statuses.map((status) => {
          const selected = status === ticket.status ? 'selected' : '';
          return `<option value="${status}" ${selected}>${labelStatus(status)}</option>`;
        }).join('');
        select.addEventListener('change', (event) => {
          updateTicket(ticket.id, { status: event.target.value });
        });

        const resolveButton = card.querySelector('[data-ticket-resolve]');
        resolveButton.addEventListener('click', () => {
          updateTicket(ticket.id, { status: 'resolved' });
        });

        column.appendChild(card);
      });

      boardColumns.querySelectorAll('[data-status-column]').forEach((column) => {
        const status = column.dataset.statusColumn;
        const count = counts.get(status) || 0;
        column.querySelector('[data-count]').textContent = count;
      });
    }

    async function refreshBoard() {
      const tickets = await fetchTickets();
      renderTickets(tickets);
    }

    async function updateTicket(id, payload) {
      if (!formStatus) return;
      try {
        formStatus.textContent = 'Updating ticket…';
        formStatus.className = 'form-status';
        await patchTicket(id, payload);
        await refreshBoard();
        formStatus.textContent = '';
      } catch (error) {
        console.error(error);
        formStatus.textContent = error.message;
        formStatus.className = 'form-status error';
      }
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
            ? 'Ticket auto-resolved instantly. Review in the Resolved column.'
            : 'Ticket created successfully.';
          formStatus.className = 'form-status success';
        }
        await refreshBoard();
      } catch (error) {
        console.error(error);
        if (formStatus) {
          formStatus.textContent = error instanceof Error ? error.message : 'Submission failed.';
          formStatus.className = 'form-status error';
        }
      }
    });

    renderColumnShells();
    refreshBoard().catch((error) => {
      if (formStatus) {
        formStatus.textContent = error.message;
        formStatus.className = 'form-status error';
      }
    });

    window.setInterval(() => {
      refreshBoard().catch((error) => {
        if (formStatus && !formStatus.textContent) {
          formStatus.textContent = error.message;
          formStatus.className = 'form-status error';
        }
      });
    }, 30000);
  }

  window.addEventListener('DOMContentLoaded', initHelpdesk);
})();
