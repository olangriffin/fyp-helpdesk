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
    if (!isoString) return '—';
    const date = new Date(isoString);
    return date.toLocaleString(undefined, {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  }

  function parseDatasetJSON(root, key, fallback) {
    try {
      const value = root.dataset[key];
      return value ? JSON.parse(value) : fallback;
    } catch (error) {
      console.warn(`Unable to parse dataset for ${key}`, error);
      return fallback;
    }
  }

  function initAdminDashboard() {
    const root = document.querySelector('[data-admin-dashboard]');
    if (!root) return;

    const statuses = parseDatasetJSON(root, 'statuses', []);
    const priorities = parseDatasetJSON(root, 'priorities', []);
    const initialStats = parseDatasetJSON(root, 'initialStats', null);

    const statsGrid = root.querySelector('[data-slot="stats-grid"]');
    const statsFlash = root.querySelector('[data-slot="stats-flash"]');
    const statusFilter = root.querySelector('[data-filter="status"]');
    const priorityFilter = root.querySelector('[data-filter="priority"]');
    const searchInput = root.querySelector('[data-filter="term"]');
    const ticketTable = root.querySelector('[data-slot="ticket-table"]');
    const tableFlash = root.querySelector('[data-slot="table-flash"]');
    const rowTemplate = root.querySelector('[data-template="ticket-row"]');
    const detailPanel = root.querySelector('[data-panel="detail"]');
    const detailSubject = root.querySelector('[data-detail="subject"]');
    const detailMeta = root.querySelector('[data-detail="meta"]');
    const detailStatus = root.querySelector('[data-detail="status"]');
    const detailAssignee = root.querySelector('[data-detail="assignee"]');
    const detailResolution = root.querySelector('[data-detail="resolution"]');
    const detailForm = root.querySelector('[data-detail="form"]');
    const detailFlash = root.querySelector('[data-detail="flash"]');
    const closeDetail = root.querySelector('[data-detail="close"]');
    const resolveButton = root.querySelector('[data-detail="resolve"]');
    const detailStatusPill = root.querySelector('[data-detail="status-pill"]');

    if (!rowTemplate || !ticketTable || !statsGrid) {
      console.warn('Admin dashboard template is missing required elements.');
      return;
    }

    let tickets = [];
    let selectedTicket = null;

    function renderStats(stats) {
      if (!stats) {
        statsGrid.innerHTML = '';
        return;
      }

      const cards = [];
      cards.push({ label: 'Total tickets', value: stats.total?.tickets ?? 0 });
      statuses.forEach((status) => {
        cards.push({ label: labelStatus(status), value: stats.status?.[status] ?? 0 });
      });
      priorities.forEach((priority) => {
        cards.push({ label: `${priority} priority`, value: stats.priority?.[priority] ?? 0 });
      });

      statsGrid.innerHTML = '';
      cards.forEach(({ label, value }) => {
        const card = document.createElement('div');
        card.className = 'stat-card';
        card.innerHTML = `<span class="label">${label}</span><strong>${value}</strong>`;
        statsGrid.appendChild(card);
      });
    }

    function applyFilters() {
      const statusValue = statusFilter?.value ?? 'all';
      const priorityValue = priorityFilter?.value ?? 'all';
      const term = searchInput?.value.trim().toLowerCase() ?? '';

      return tickets.filter((ticket) => {
        const matchesStatus = statusValue === 'all' || ticket.status === statusValue;
        const matchesPriority = priorityValue === 'all' || ticket.priority === priorityValue;
        const matchesTerm = !term || [ticket.subject, ticket.description, ticket.requester, ticket.issue_type]
          .some((field) => field && field.toLowerCase().includes(term));
        return matchesStatus && matchesPriority && matchesTerm;
      });
    }

    function renderTable() {
      const filtered = applyFilters();
      ticketTable.innerHTML = '';

      if (!filtered.length) {
        const emptyRow = document.createElement('tr');
        const cell = document.createElement('td');
        cell.colSpan = 7;
        cell.className = 'table-empty-row';
        cell.textContent = 'No tickets match the current filters.';
        emptyRow.appendChild(cell);
        ticketTable.appendChild(emptyRow);
        return;
      }

      filtered.forEach((ticket) => {
        const row = rowTemplate.content.firstElementChild.cloneNode(true);
        row.dataset.ticketId = ticket.id;
        row.querySelector('[data-cell="subject"]').textContent = ticket.subject;
        row.querySelector('[data-cell="requester"]').textContent = ticket.requester;
        const statusCell = row.querySelector('[data-cell="status"]');
        statusCell.textContent = labelStatus(ticket.status);
        statusCell.dataset.status = ticket.status;
        const priorityCell = row.querySelector('[data-cell="priority"]');
        priorityCell.textContent = ticket.priority;
        priorityCell.dataset.priority = ticket.priority;
        row.querySelector('[data-cell="assignee"]').textContent = ticket.assignee || 'Unassigned';
        row.querySelector('[data-cell="updated"]').textContent = formatDate(ticket.updated_at);

        row.addEventListener('click', () => {
          showDetail(ticket.id);
        });

        const manageButton = row.querySelector('[data-action="manage"]');
        manageButton.addEventListener('click', (event) => {
          event.preventDefault();
          event.stopPropagation();
          showDetail(ticket.id);
        });

        ticketTable.appendChild(row);
      });
    }

    function populateStatusSelect(select, value) {
      if (!select) return;
      select.innerHTML = statuses.map((status) => {
        const selected = status === value ? 'selected' : '';
        return `<option value="${status}" ${selected}>${labelStatus(status)}</option>`;
      }).join('');
    }

    function showDetail(ticketId) {
      selectedTicket = tickets.find((ticket) => ticket.id === ticketId);
      if (!selectedTicket) return;

      detailPanel?.classList.remove('is-hidden');
      detailSubject.textContent = selectedTicket.subject;
      if (detailStatusPill) {
        detailStatusPill.textContent = labelStatus(selectedTicket.status);
        detailStatusPill.dataset.status = selectedTicket.status;
      }
      detailMeta.innerHTML = `
        <span><strong>Requester:</strong> ${selectedTicket.requester}</span>
        <span><strong>Issue type:</strong> ${selectedTicket.issue_type.replace(/_/g, ' ')}</span>
        <span><strong>Priority:</strong> ${selectedTicket.priority}</span>
        <span><strong>Created:</strong> ${formatDate(selectedTicket.created_at)}</span>
        <span><strong>Updated:</strong> ${formatDate(selectedTicket.updated_at)}</span>
      `;
      populateStatusSelect(detailStatus, selectedTicket.status);
      detailAssignee.value = selectedTicket.assignee || '';
      detailResolution.value = selectedTicket.resolution_notes || '';
      detailFlash.textContent = '';
      detailFlash.className = 'flash';
    }

    async function refreshStats() {
      try {
        if (statsFlash) {
          statsFlash.textContent = 'Refreshing…';
          statsFlash.className = 'flash';
        }
        const response = await fetch('/tickets/stats');
        if (!response.ok) throw new Error('Unable to load stats');
        const stats = await response.json();
        renderStats(stats);
        if (statsFlash) {
          statsFlash.textContent = '';
        }
      } catch (error) {
        if (statsFlash) {
          statsFlash.textContent = error.message;
          statsFlash.className = 'flash error';
        }
      }
    }

    async function refreshTickets() {
      try {
        if (tableFlash) {
          tableFlash.textContent = 'Refreshing…';
          tableFlash.className = 'flash';
        }
        const response = await fetch('/tickets');
        if (!response.ok) throw new Error('Unable to load tickets');
        tickets = await response.json();
        renderTable();
        if (tableFlash) {
          tableFlash.textContent = '';
        }
        if (selectedTicket) {
          const updated = tickets.find((ticket) => ticket.id === selectedTicket.id);
          if (updated) {
            selectedTicket = updated;
            showDetail(updated.id);
          }
        }
      } catch (error) {
        if (tableFlash) {
          tableFlash.textContent = error.message;
          tableFlash.className = 'flash error';
        }
      }
    }

    async function saveTicketChanges(payload) {
      if (!selectedTicket) return;
      detailFlash.textContent = 'Saving…';
      detailFlash.className = 'flash';
      const response = await fetch(`/tickets/${selectedTicket.id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new Error(error.detail || 'Unable to update ticket');
      }
      detailFlash.textContent = 'Changes saved';
      detailFlash.className = 'flash success';
      await Promise.all([refreshTickets(), refreshStats()]);
    }

    detailForm?.addEventListener('submit', async (event) => {
      event.preventDefault();
      try {
        await saveTicketChanges({
          status: detailStatus.value,
          assignee: detailAssignee.value || null,
          resolution_notes: detailResolution.value || null,
        });
      } catch (error) {
        detailFlash.textContent = error.message;
        detailFlash.className = 'flash error';
      }
    });

    resolveButton?.addEventListener('click', async () => {
      if (!selectedTicket) return;
      try {
        await saveTicketChanges({
          status: 'resolved',
          resolution_notes: detailResolution.value || selectedTicket.resolution_notes || 'Resolved via dashboard action.',
        });
      } catch (error) {
        detailFlash.textContent = error.message;
        detailFlash.className = 'flash error';
      }
    });

    closeDetail?.addEventListener('click', () => {
      detailPanel?.classList.add('is-hidden');
      selectedTicket = null;
    });

    statusFilter?.addEventListener('change', renderTable);
    priorityFilter?.addEventListener('change', renderTable);
    if (searchInput) {
      searchInput.addEventListener('input', () => {
        window.clearTimeout(searchInput._timeout);
        searchInput._timeout = window.setTimeout(renderTable, 150);
      });
    }

    if (initialStats) {
      renderStats(initialStats);
    }

    refreshStats();
    refreshTickets();
    window.setInterval(() => {
      refreshTickets();
      refreshStats();
    }, 30000);
  }

  window.addEventListener('DOMContentLoaded', initAdminDashboard);
})();
