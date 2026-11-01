/**
 * app.js - Frontend Client Controller for NexusAI Software Management System
 * Reactive REST API client, Chart.js managers, modal controllers, and AI chatbot.
 */

// ==========================================================================
// Theme Management (Dark / Light)
// ==========================================================================
function initTheme() {
  const savedTheme = localStorage.getItem('nexus_theme') || 'dark';
  document.documentElement.setAttribute('data-theme', savedTheme);
  updateThemeIcon(savedTheme);
}

function toggleTheme() {
  const current = document.documentElement.getAttribute('data-theme') || 'dark';
  const nextTheme = current === 'dark' ? 'light' : 'dark';
  document.documentElement.setAttribute('data-theme', nextTheme);
  localStorage.setItem('nexus_theme', nextTheme);
  updateThemeIcon(nextTheme);

  // Re-render any active charts with new theme colors
  if (window.renderDashboardCharts) window.renderDashboardCharts();
  if (window.renderReportCharts) window.renderReportCharts();
}

function updateThemeIcon(theme) {
  const btn = document.getElementById('themeToggleBtn');
  if (!btn) return;
  if (theme === 'dark') {
    btn.innerHTML = `<i data-lucide="sun"></i>`;
  } else {
    btn.innerHTML = `<i data-lucide="moon"></i>`;
  }
  if (window.lucide) lucide.createIcons();
}

// ==========================================================================
// Toast Notification Engine
// ==========================================================================
function showToast(message, type = 'info') {
  let container = document.getElementById('toastContainer');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toastContainer';
    container.className = 'toast-container';
    document.body.appendChild(container);
  }

  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  
  let iconName = 'info';
  if (type === 'success') iconName = 'check-circle';
  if (type === 'error') iconName = 'alert-triangle';
  if (type === 'warning') iconName = 'alert-circle';

  toast.innerHTML = `
    <i data-lucide="${iconName}"></i>
    <span>${message}</span>
  `;
  container.appendChild(toast);
  if (window.lucide) lucide.createIcons();

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(100%)';
    toast.style.transition = 'all 0.3s ease';
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

// ==========================================================================
// Modal Controllers
// ==========================================================================
function openModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) {
    modal.classList.add('open');
    if (window.lucide) lucide.createIcons();
  }
}

function closeModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) {
    modal.classList.remove('open');
  }
}

// Close modal when clicking outside dialog
document.addEventListener('click', (e) => {
  if (e.target.classList.contains('modal-overlay')) {
    e.target.classList.remove('open');
  }
});

// ==========================================================================
// Sidebar Mobile Toggle
// ==========================================================================
function toggleMobileMenu() {
  const sidebar = document.getElementById('sidebar');
  if (sidebar) {
    sidebar.classList.toggle('open');
  }
}

// ==========================================================================
// DASHBOARD CONTROLLER
// ==========================================================================
let statusChartInstance = null;
let taskPriorityChartInstance = null;

async function loadDashboard() {
  try {
    const res = await fetch('/api/dashboard');
    const data = await res.json();
    if (!data.success) return;

    const m = data.metrics;

    // Populate Metrics
    const setElem = (id, val) => {
      const el = document.getElementById(id);
      if (el) el.innerText = val;
    };

    setElem('kpiTotalProjects', m.total_projects);
    setElem('kpiActiveProjects', m.active_projects);
    setElem('kpiPendingTasks', m.pending_tasks);
    setElem('kpiCompletedTasks', m.completed_tasks);
    setElem('kpiTeamMembers', m.total_team_members);
    setElem('kpiProgressPct', `${m.overall_progress_pct}%`);

    const pFill = document.getElementById('kpiProgressFill');
    if (pFill) pFill.style.width = `${m.overall_progress_pct}%`;

    // Render Charts
    window.renderDashboardCharts = () => {
      renderStatusChart(data.charts.project_status);
      renderTaskPriorityChart(data.charts.task_priority);
    };
    window.renderDashboardCharts();

    // Upcoming Deadlines
    const deadlineList = document.getElementById('upcomingDeadlinesList');
    if (deadlineList) {
      if (!data.upcoming_deadlines || data.upcoming_deadlines.length === 0) {
        deadlineList.innerHTML = `<div class="empty-state">No pending upcoming deadlines.</div>`;
      } else {
        deadlineList.innerHTML = data.upcoming_deadlines.map(t => {
          const pClass = (t.priority || 'medium').toLowerCase();
          return `
            <div class="deadline-item ${pClass}">
              <div class="deadline-left">
                <div class="deadline-title">${escapeHtml(t.title)}</div>
                <div class="deadline-sub">Project: <strong>${escapeHtml(t.project_name)}</strong> • Assigned: ${escapeHtml(t.assignee_name || 'Unassigned')}</div>
              </div>
              <div style="text-align: right;">
                <span class="badge badge-${pClass}">${t.priority}</span>
                <div style="font-size: 0.72rem; color: var(--text-muted); margin-top: 4px;">📅 ${t.due_date}</div>
              </div>
            </div>
          `;
        }).join('');
      }
    }

    // Recent Activities
    const activityList = document.getElementById('recentActivityStream');
    if (activityList) {
      if (!data.recent_activities || data.recent_activities.length === 0) {
        activityList.innerHTML = `<div class="empty-state">No recent activities logged yet.</div>`;
      } else {
        activityList.innerHTML = data.recent_activities.map(a => {
          let icon = 'activity';
          let colorBg = 'var(--primary-light)';
          let colorText = 'var(--primary)';
          if (a.action_type.includes('task')) { icon = 'check-square'; colorBg = 'var(--success-bg)'; colorText = 'var(--success)'; }
          if (a.action_type.includes('project')) { icon = 'folder'; colorBg = 'var(--info-bg)'; colorText = 'var(--info)'; }
          if (a.action_type.includes('alert')) { icon = 'alert-triangle'; colorBg = 'var(--danger-bg)'; colorText = 'var(--danger)'; }

          return `
            <div class="activity-item">
              <div class="activity-icon-bullet" style="background:${colorBg}; color:${colorText}">
                <i data-lucide="${icon}"></i>
              </div>
              <div class="activity-content">
                <div class="activity-text">${escapeHtml(a.description)}</div>
                <div class="activity-time">${formatTimeAgo(a.created_at)}</div>
              </div>
            </div>
          `;
        }).join('');
      }
    }

    if (window.lucide) lucide.createIcons();

  } catch (err) {
    console.error('Error loading dashboard:', err);
  }
}

function renderStatusChart(statusData) {
  const ctx = document.getElementById('projectStatusChart');
  if (!ctx) return;

  if (statusChartInstance) statusChartInstance.destroy();

  const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
  const textColor = isDark ? '#94a3b8' : '#475569';

  statusChartInstance = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: ['In Progress', 'Completed', 'Not Started', 'On Hold'],
      datasets: [{
        data: [
          statusData['In Progress'] || 0,
          statusData['Completed'] || 0,
          statusData['Not Started'] || 0,
          statusData['On Hold'] || 0
        ],
        backgroundColor: ['#6366f1', '#10b981', '#64748b', '#f59e0b'],
        borderWidth: 2,
        borderColor: isDark ? '#131b2e' : '#ffffff'
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'bottom',
          labels: { color: textColor, font: { family: 'Plus Jakarta Sans', size: 12 } }
        }
      },
      cutout: '70%'
    }
  });
}

function renderTaskPriorityChart(priorityData) {
  const ctx = document.getElementById('taskPriorityChart');
  if (!ctx) return;

  if (taskPriorityChartInstance) taskPriorityChartInstance.destroy();

  const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
  const textColor = isDark ? '#94a3b8' : '#475569';
  const gridColor = isDark ? 'rgba(255, 255, 255, 0.06)' : '#e2e8f0';

  taskPriorityChartInstance = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: ['Urgent', 'High', 'Medium', 'Low'],
      datasets: [{
        label: 'Active Tasks by Priority',
        data: [
          priorityData['Urgent'] || 0,
          priorityData['High'] || 0,
          priorityData['Medium'] || 0,
          priorityData['Low'] || 0
        ],
        backgroundColor: ['#ef4444', '#f59e0b', '#6366f1', '#94a3b8'],
        borderRadius: 6
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false }
      },
      scales: {
        x: {
          ticks: { color: textColor, font: { family: 'Plus Jakarta Sans' } },
          grid: { display: false }
        },
        y: {
          ticks: { color: textColor, stepSize: 1 },
          grid: { color: gridColor }
        }
      }
    }
  });
}

// ==========================================================================
// PROJECTS CONTROLLER
// ==========================================================================
let allProjects = [];

async function loadProjects() {
  try {
    const statusFilter = document.getElementById('projectStatusFilter')?.value || 'All';
    const priorityFilter = document.getElementById('projectPriorityFilter')?.value || 'All';
    const searchQuery = document.getElementById('projectSearchInput')?.value || '';

    const url = `/api/projects?status=${encodeURIComponent(statusFilter)}&priority=${encodeURIComponent(priorityFilter)}&search=${encodeURIComponent(searchQuery)}`;
    const res = await fetch(url);
    const data = await res.json();
    if (!data.success) return;

    allProjects = data.projects;
    renderProjectsGrid(allProjects);

  } catch (err) {
    console.error('Error loading projects:', err);
  }
}

function renderProjectsGrid(projects) {
  const grid = document.getElementById('projectsGrid');
  if (!grid) return;

  if (projects.length === 0) {
    grid.innerHTML = `
      <div style="grid-column: 1/-1; text-align: center; padding: 48px; background: var(--bg-card); border-radius: var(--radius-lg); border: 1px solid var(--border-color);">
        <i data-lucide="folder-x" style="width: 48px; height: 48px; color: var(--text-muted); margin-bottom: 12px;"></i>
        <h3 style="font-size: 1.1rem; color: var(--text-primary); margin-bottom: 6px;">No projects found</h3>
        <p style="font-size: 0.85rem; color: var(--text-secondary); margin-bottom: 16px;">Try adjusting filters or create a new project.</p>
        <button class="btn btn-primary" onclick="openCreateProjectModal()">Create Project</button>
      </div>
    `;
    if (window.lucide) lucide.createIcons();
    return;
  }

  grid.innerHTML = projects.map(p => {
    const statusClass = p.status.toLowerCase().replace(' ', '-');
    const priorityClass = p.priority.toLowerCase();

    const memberAvatars = (p.members || []).map(m => `
      <img src="${m.avatar || 'https://api.dicebear.com/7.x/avataaars/svg?seed=' + m.name}" class="avatar-stack-img" title="${escapeHtml(m.name)} - ${escapeHtml(m.role)}" alt="${escapeHtml(m.name)}">
    `).join('');

    return `
      <div class="project-card" onclick="viewProjectDetails(${p.id})">
        <div>
          <div class="project-card-top">
            <span class="badge badge-${statusClass}">${p.status}</span>
            <span class="badge badge-${priorityClass}">${p.priority}</span>
          </div>
          <h3 class="project-card-title" style="margin-top: 10px;">${escapeHtml(p.name)}</h3>
          <p class="project-card-desc" style="margin-top: 6px;">${escapeHtml(p.description || 'No description provided.')}</p>
        </div>

        <div>
          <div style="display: flex; justify-content: space-between; font-size: 0.78rem; font-weight: 600; margin-bottom: 4px;">
            <span>Progress</span>
            <span>${p.completed_tasks}/${p.total_tasks} tasks (${p.progress_pct}%)</span>
          </div>
          <div class="progress-container">
            <div class="progress-bar-fill" style="width: ${p.progress_pct}%"></div>
          </div>

          <div class="project-meta-row" style="margin-top: 12px;">
            <div class="avatar-stack">
              ${memberAvatars || '<span style="font-size: 0.75rem; color: var(--text-muted);">No members</span>'}
            </div>
            <span>📅 ${p.end_date}</span>
          </div>

          <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 14px; padding-top: 12px; border-top: 1px solid var(--border-color);" onclick="event.stopPropagation();">
            <span style="font-size: 0.82rem; font-weight: 700; color: var(--primary);">$${(p.budget || 0).toLocaleString()}</span>
            <div style="display: flex; gap: 8px;">
              <button class="btn btn-secondary btn-sm" onclick="editProject(${p.id})"><i data-lucide="edit-3"></i> Edit</button>
              <button class="btn btn-outline btn-sm" style="color: var(--danger); border-color: rgba(239, 68, 68, 0.3);" onclick="confirmDeleteProject(${p.id}, '${escapeHtml(p.name)}')"><i data-lucide="trash-2"></i></button>
            </div>
          </div>
        </div>
      </div>
    `;
  }).join('');

  if (window.lucide) lucide.createIcons();
}

// Create / Edit Project
async function openCreateProjectModal() {
  document.getElementById('projectModalTitle').innerText = 'Create New Project';
  document.getElementById('projectForm').reset();
  document.getElementById('projectIdInput').value = '';
  await populateTeamSelects();
  openModal('projectModal');
}

async function editProject(projectId) {
  try {
    const res = await fetch(`/api/projects/${projectId}`);
    const data = await res.json();
    if (!data.success) return;

    const p = data.project;
    document.getElementById('projectModalTitle').innerText = 'Edit Project';
    document.getElementById('projectIdInput').value = p.id;
    document.getElementById('projectNameInput').value = p.name;
    document.getElementById('projectDescInput').value = p.description || '';
    document.getElementById('projectStatusSelect').value = p.status;
    document.getElementById('projectPrioritySelect').value = p.priority;
    document.getElementById('projectStartDateInput').value = p.start_date;
    document.getElementById('projectEndDateInput').value = p.end_date;
    document.getElementById('projectBudgetInput').value = p.budget || 0;

    await populateTeamSelects(p.lead_id, (p.members || []).map(m => m.id));
    openModal('projectModal');
  } catch (err) {
    showToast('Failed to load project details', 'error');
  }
}

async function handleProjectFormSubmit(e) {
  e.preventDefault();
  const id = document.getElementById('projectIdInput').value;
  const name = document.getElementById('projectNameInput').value.trim();
  const description = document.getElementById('projectDescInput').value.trim();
  const status = document.getElementById('projectStatusSelect').value;
  const priority = document.getElementById('projectPrioritySelect').value;
  const start_date = document.getElementById('projectStartDateInput').value;
  const end_date = document.getElementById('projectEndDateInput').value;
  const budget = parseFloat(document.getElementById('projectBudgetInput').value) || 0;
  const lead_id = parseInt(document.getElementById('projectLeadSelect').value) || null;

  // Selected members
  const memberSelect = document.getElementById('projectMembersSelect');
  const member_ids = Array.from(memberSelect.selectedOptions).map(opt => parseInt(opt.value));

  const payload = { name, description, status, priority, start_date, end_date, budget, lead_id, member_ids };
  const method = id ? 'PUT' : 'POST';
  const url = id ? `/api/projects/${id}` : '/api/projects';

  try {
    const res = await fetch(url, {
      method,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const result = await res.json();

    if (result.success) {
      showToast(result.message || 'Project saved successfully', 'success');
      closeModal('projectModal');
      loadProjects();
    } else {
      showToast(result.error || 'Failed to save project', 'error');
    }
  } catch (err) {
    showToast('Network error while saving project', 'error');
  }
}

function confirmDeleteProject(id, name) {
  if (confirm(`Are you sure you want to delete project "${name}"? All associated tasks will also be deleted.`)) {
    deleteProject(id);
  }
}

async function deleteProject(id) {
  try {
    const res = await fetch(`/api/projects/${id}`, { method: 'DELETE' });
    const data = await res.json();
    if (data.success) {
      showToast('Project deleted successfully', 'success');
      loadProjects();
    } else {
      showToast(data.error || 'Failed to delete project', 'error');
    }
  } catch (err) {
    showToast('Error deleting project', 'error');
  }
}

// Project Details Modal
async function viewProjectDetails(projectId) {
  try {
    const res = await fetch(`/api/projects/${projectId}`);
    const data = await res.json();
    if (!data.success) return;

    const p = data.project;
    document.getElementById('projectDetailTitle').innerText = p.name;
    document.getElementById('projectDetailDesc').innerText = p.description || 'No description provided.';
    document.getElementById('projectDetailStatus').innerText = p.status;
    document.getElementById('projectDetailStatus').className = `badge badge-${p.status.toLowerCase().replace(' ', '-')}`;
    document.getElementById('projectDetailPriority').innerText = p.priority;
    document.getElementById('projectDetailPriority').className = `badge badge-${p.priority.toLowerCase()}`;
    document.getElementById('projectDetailDates').innerText = `${p.start_date} to ${p.end_date}`;
    document.getElementById('projectDetailBudget').innerText = `$${(p.budget || 0).toLocaleString()}`;
    document.getElementById('projectDetailLead').innerText = p.lead_name || 'No Lead Assigned';
    document.getElementById('projectDetailProgressText').innerText = `${p.completed_tasks}/${p.total_tasks} tasks completed (${p.progress_pct}%)`;
    document.getElementById('projectDetailProgressFill').style.width = `${p.progress_pct}%`;

    const taskList = document.getElementById('projectDetailTasksList');
    if (taskList) {
      if (!p.tasks || p.tasks.length === 0) {
        taskList.innerHTML = `<div style="color: var(--text-muted); font-size: 0.85rem; padding: 12px 0;">No tasks created for this project yet.</div>`;
      } else {
        taskList.innerHTML = p.tasks.map(t => `
          <div style="display: flex; align-items: center; justify-content: space-between; padding: 8px 12px; background: var(--bg-tertiary); border-radius: var(--radius-md); font-size: 0.85rem;">
            <div style="display: flex; align-items: center; gap: 8px;">
              <input type="checkbox" ${t.status === 'Completed' ? 'checked' : ''} onchange="toggleTaskStatus(${t.id}, this.checked)" style="cursor: pointer;">
              <span style="${t.status === 'Completed' ? 'text-decoration: line-through; color: var(--text-muted);' : ''}">${escapeHtml(t.title)}</span>
            </div>
            <div style="display: flex; align-items: center; gap: 8px;">
              <span class="badge badge-${t.priority.toLowerCase()}">${t.priority}</span>
              <span style="font-size: 0.74rem; color: var(--text-muted);">Due: ${t.due_date}</span>
            </div>
          </div>
        `).join('');
      }
    }

    openModal('projectDetailModal');
    if (window.lucide) lucide.createIcons();

  } catch (err) {
    showToast('Failed to load project details', 'error');
  }
}

// ==========================================================================
// TASKS CONTROLLER (Kanban + List)
// ==========================================================================
let allTasks = [];
let currentTaskViewMode = 'kanban';

async function loadTasks() {
  try {
    const projectFilter = document.getElementById('taskProjectFilter')?.value || 'All';
    const statusFilter = document.getElementById('taskStatusFilter')?.value || 'All';
    const priorityFilter = document.getElementById('taskPriorityFilter')?.value || 'All';
    const searchQuery = document.getElementById('taskSearchInput')?.value || '';

    // Populate project filter dropdown if not already populated
    const pFilterEl = document.getElementById('taskProjectFilter');
    if (pFilterEl && pFilterEl.options.length <= 1) {
      const pRes = await fetch('/api/projects');
      const pData = await pRes.json();
      if (pData.success) {
        pFilterEl.innerHTML = '<option value="All">All Projects</option>' +
          pData.projects.map(p => `<option value="${p.id}">${escapeHtml(p.name)}</option>`).join('');
      }
    }

    const url = `/api/tasks?project_id=${encodeURIComponent(projectFilter)}&status=${encodeURIComponent(statusFilter)}&priority=${encodeURIComponent(priorityFilter)}&search=${encodeURIComponent(searchQuery)}`;
    const res = await fetch(url);
    const data = await res.json();
    if (!data.success) return;

    allTasks = data.tasks;
    renderTasks();

  } catch (err) {
    console.error('Error loading tasks:', err);
  }
}

function setTaskView(mode) {
  currentTaskViewMode = mode;
  document.getElementById('kanbanViewBtn')?.classList.toggle('active', mode === 'kanban');
  document.getElementById('listViewBtn')?.classList.toggle('active', mode === 'list');
  renderTasks();
}

function renderTasks() {
  if (currentTaskViewMode === 'kanban') {
    renderKanbanBoard(allTasks);
  } else {
    renderTasksTable(allTasks);
  }
}

function renderKanbanBoard(tasks) {
  const container = document.getElementById('tasksContainer');
  if (!container) return;

  const columns = ['To Do', 'In Progress', 'Review', 'Completed'];

  container.innerHTML = `
    <div class="kanban-board">
      ${columns.map(col => {
        const colTasks = tasks.filter(t => t.status === col);
        return `
          <div class="kanban-col">
            <div class="kanban-col-header">
              <span>${col}</span>
              <span class="col-count-badge">${colTasks.length}</span>
            </div>
            <div class="kanban-task-list">
              ${colTasks.map(t => renderKanbanCard(t)).join('')}
              ${colTasks.length === 0 ? '<div style="color: var(--text-muted); font-size: 0.8rem; text-align: center; padding: 24px 0;">No tasks</div>' : ''}
            </div>
          </div>
        `;
      }).join('')}
    </div>
  `;

  if (window.lucide) lucide.createIcons();
}

function renderKanbanCard(t) {
  const priorityClass = t.priority.toLowerCase();
  return `
    <div class="kanban-task-card">
      <div style="display: flex; justify-content: space-between; align-items: flex-start;">
        <span class="task-project-pill">${escapeHtml(t.project_name)}</span>
        <span class="badge badge-${priorityClass}">${t.priority}</span>
      </div>

      <div class="kanban-task-title">${escapeHtml(t.title)}</div>
      ${t.description ? `<div style="font-size: 0.78rem; color: var(--text-secondary);">${escapeHtml(t.description)}</div>` : ''}

      <div class="kanban-task-footer">
        <div style="display: flex; align-items: center; gap: 6px;">
          <img src="${t.assignee_avatar || 'https://api.dicebear.com/7.x/avataaars/svg?seed=' + (t.assignee_name || 'user')}" style="width: 22px; height: 22px; border-radius: 50%;" alt="${escapeHtml(t.assignee_name || '')}">
          <span>${escapeHtml(t.assignee_name || 'Unassigned')}</span>
        </div>
        <span>📅 ${t.due_date}</span>
      </div>

      <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 6px; padding-top: 6px; border-top: 1px dashed var(--border-color);">
        <select onchange="updateTaskStatusFast(${t.id}, this.value)" style="font-size: 0.72rem; background: var(--bg-tertiary); border: 1px solid var(--border-color); color: var(--text-primary); border-radius: 4px; padding: 2px 4px; cursor: pointer;">
          <option value="To Do" ${t.status === 'To Do' ? 'selected' : ''}>To Do</option>
          <option value="In Progress" ${t.status === 'In Progress' ? 'selected' : ''}>In Progress</option>
          <option value="Review" ${t.status === 'Review' ? 'selected' : ''}>Review</option>
          <option value="Completed" ${t.status === 'Completed' ? 'selected' : ''}>Completed</option>
        </select>
        <div style="display: flex; gap: 4px;">
          <button class="icon-btn" style="width: 26px; height: 26px;" onclick="editTask(${t.id})"><i data-lucide="edit-2" style="width: 14px; height: 14px;"></i></button>
          <button class="icon-btn" style="width: 26px; height: 26px; color: var(--danger);" onclick="confirmDeleteTask(${t.id}, '${escapeHtml(t.title)}')"><i data-lucide="trash" style="width: 14px; height: 14px;"></i></button>
        </div>
      </div>
    </div>
  `;
}

function renderTasksTable(tasks) {
  const container = document.getElementById('tasksContainer');
  if (!container) return;

  container.innerHTML = `
    <div style="background: var(--bg-card); border-radius: var(--radius-lg); border: 1px solid var(--border-color); overflow-x: auto;">
      <table style="width: 100%; border-collapse: collapse; font-size: 0.88rem; text-align: left;">
        <thead>
          <tr style="border-bottom: 1px solid var(--border-color); color: var(--text-muted); font-size: 0.76rem; text-transform: uppercase;">
            <th style="padding: 14px 18px;">Task Title</th>
            <th style="padding: 14px 18px;">Project</th>
            <th style="padding: 14px 18px;">Assignee</th>
            <th style="padding: 14px 18px;">Priority</th>
            <th style="padding: 14px 18px;">Status</th>
            <th style="padding: 14px 18px;">Due Date</th>
            <th style="padding: 14px 18px; text-align: right;">Actions</th>
          </tr>
        </thead>
        <tbody>
          ${tasks.map(t => `
            <tr style="border-bottom: 1px solid var(--border-color); transition: background 0.15s ease;" onmouseover="this.style.background='var(--bg-tertiary)'" onmouseout="this.style.background='transparent'">
              <td style="padding: 14px 18px; font-weight: 600; color: var(--text-primary);">${escapeHtml(t.title)}</td>
              <td style="padding: 14px 18px; color: var(--primary); font-weight: 500;">${escapeHtml(t.project_name)}</td>
              <td style="padding: 14px 18px;">
                <div style="display: flex; align-items: center; gap: 8px;">
                  <img src="${t.assignee_avatar || 'https://api.dicebear.com/7.x/avataaars/svg?seed=' + (t.assignee_name || 'user')}" style="width: 24px; height: 24px; border-radius: 50%;" alt="${escapeHtml(t.assignee_name || '')}">
                  <span>${escapeHtml(t.assignee_name || 'Unassigned')}</span>
                </div>
              </td>
              <td style="padding: 14px 18px;"><span class="badge badge-${t.priority.toLowerCase()}">${t.priority}</span></td>
              <td style="padding: 14px 18px;"><span class="badge badge-${t.status.toLowerCase().replace(' ', '-')}">${t.status}</span></td>
              <td style="padding: 14px 18px; font-size: 0.8rem; color: var(--text-muted);">${t.due_date}</td>
              <td style="padding: 14px 18px; text-align: right;">
                <button class="btn btn-secondary btn-sm" onclick="editTask(${t.id})">Edit</button>
                <button class="btn btn-outline btn-sm" style="color: var(--danger);" onclick="confirmDeleteTask(${t.id}, '${escapeHtml(t.title)}')">Delete</button>
              </td>
            </tr>
          `).join('')}
        </tbody>
      </table>
    </div>
  `;
}

async function updateTaskStatusFast(taskId, newStatus) {
  try {
    const res = await fetch(`/api/tasks/${taskId}`);
    const data = await res.json();
    if (!data.success) return;

    const t = data.task;
    t.status = newStatus;

    const updateRes = await fetch(`/api/tasks/${taskId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(t)
    });
    const result = await updateRes.json();
    if (result.success) {
      showToast(`Task moved to ${newStatus}`, 'success');
      loadTasks();
    }
  } catch (err) {
    showToast('Failed to update task status', 'error');
  }
}

async function toggleTaskStatus(taskId, isChecked) {
  const newStatus = isChecked ? 'Completed' : 'To Do';
  await updateTaskStatusFast(taskId, newStatus);
}

async function openCreateTaskModal() {
  document.getElementById('taskModalTitle').innerText = 'Create New Task';
  document.getElementById('taskForm').reset();
  document.getElementById('taskIdInput').value = '';
  await populateProjectAndTeamSelects();
  openModal('taskModal');
}

async function editTask(taskId) {
  try {
    const res = await fetch(`/api/tasks/${taskId}`);
    const data = await res.json();
    if (!data.success) return;

    const t = data.task;
    document.getElementById('taskModalTitle').innerText = 'Edit Task';
    document.getElementById('taskIdInput').value = t.id;
    document.getElementById('taskTitleInput').value = t.title;
    document.getElementById('taskDescInput').value = t.description || '';
    document.getElementById('taskStatusSelect').value = t.status;
    document.getElementById('taskPrioritySelect').value = t.priority;
    document.getElementById('taskDueDateInput').value = t.due_date;
    document.getElementById('taskHoursInput').value = t.estimated_hours || 0;

    await populateProjectAndTeamSelects(t.project_id, t.assigned_to);
    openModal('taskModal');
  } catch (err) {
    showToast('Failed to load task details', 'error');
  }
}

async function handleTaskFormSubmit(e) {
  e.preventDefault();
  const id = document.getElementById('taskIdInput').value;
  const title = document.getElementById('taskTitleInput').value.trim();
  const description = document.getElementById('taskDescInput').value.trim();
  const project_id = parseInt(document.getElementById('taskProjectSelect').value);
  const assigned_to = parseInt(document.getElementById('taskAssigneeSelect').value) || null;
  const status = document.getElementById('taskStatusSelect').value;
  const priority = document.getElementById('taskPrioritySelect').value;
  const due_date = document.getElementById('taskDueDateInput').value;
  const estimated_hours = parseFloat(document.getElementById('taskHoursInput').value) || 0;

  const payload = { title, description, project_id, assigned_to, status, priority, due_date, estimated_hours };
  const method = id ? 'PUT' : 'POST';
  const url = id ? `/api/tasks/${id}` : '/api/tasks';

  try {
    const res = await fetch(url, {
      method,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const result = await res.json();

    if (result.success) {
      showToast(result.message || 'Task saved successfully', 'success');
      closeModal('taskModal');
      loadTasks();
    } else {
      showToast(result.error || 'Failed to save task', 'error');
    }
  } catch (err) {
    showToast('Network error while saving task', 'error');
  }
}

function confirmDeleteTask(id, title) {
  if (confirm(`Are you sure you want to delete task "${title}"?`)) {
    deleteTask(id);
  }
}

async function deleteTask(id) {
  try {
    const res = await fetch(`/api/tasks/${id}`, { method: 'DELETE' });
    const data = await res.json();
    if (data.success) {
      showToast('Task deleted successfully', 'success');
      loadTasks();
    } else {
      showToast(data.error || 'Failed to delete task', 'error');
    }
  } catch (err) {
    showToast('Error deleting task', 'error');
  }
}

// ==========================================================================
// TEAM CONTROLLER
// ==========================================================================
let allTeamMembers = [];

async function loadTeam() {
  try {
    const res = await fetch('/api/team');
    const data = await res.json();
    if (!data.success) return;

    allTeamMembers = data.team;
    renderTeamGrid(allTeamMembers);

  } catch (err) {
    console.error('Error loading team:', err);
  }
}

function renderTeamGrid(team) {
  const grid = document.getElementById('teamGrid');
  if (!grid) return;

  grid.innerHTML = team.map(m => `
    <div class="team-card">
      <img src="${m.avatar || 'https://api.dicebear.com/7.x/avataaars/svg?seed=' + m.name}" class="team-avatar-lg" alt="${escapeHtml(m.name)}">
      <div>
        <h3 class="team-name">${escapeHtml(m.name)}</h3>
        <div class="team-role">${escapeHtml(m.role)}</div>
      </div>
      <span class="team-dept-pill">${escapeHtml(m.department)}</span>

      <div class="team-stats-row">
        <div class="team-stat-item">
          <span class="team-stat-val">${m.total_tasks}</span>
          <span class="team-stat-lbl">Tasks</span>
        </div>
        <div class="team-stat-item">
          <span class="team-stat-val" style="color: var(--success);">${m.completed_tasks}</span>
          <span class="team-stat-lbl">Done</span>
        </div>
        <div class="team-stat-item">
          <span class="team-stat-val" style="color: var(--primary);">${m.completion_rate}%</span>
          <span class="team-stat-lbl">Rate</span>
        </div>
      </div>

      <div style="display: flex; gap: 8px; margin-top: 8px; width: 100%;">
        <button class="btn btn-secondary btn-sm" style="flex: 1;" onclick="editTeamMember(${m.id})">Edit</button>
        <button class="btn btn-outline btn-sm" style="color: var(--danger);" onclick="confirmDeleteTeamMember(${m.id}, '${escapeHtml(m.name)}')"><i data-lucide="trash-2"></i></button>
      </div>
    </div>
  `).join('');

  if (window.lucide) lucide.createIcons();
}

function openCreateTeamModal() {
  document.getElementById('teamModalTitle').innerText = 'Add Team Member';
  document.getElementById('teamForm').reset();
  document.getElementById('memberIdInput').value = '';
  openModal('teamModal');
}

async function editTeamMember(memberId) {
  try {
    const res = await fetch(`/api/team/${memberId}`);
    const data = await res.json();
    if (!data.success) return;

    const m = data.member;
    document.getElementById('teamModalTitle').innerText = 'Edit Team Member';
    document.getElementById('memberIdInput').value = m.id;
    document.getElementById('memberNameInput').value = m.name;
    document.getElementById('memberEmailInput').value = m.email;
    document.getElementById('memberRoleInput').value = m.role;
    document.getElementById('memberDeptSelect').value = m.department;
    document.getElementById('memberPhoneInput').value = m.phone || '';
    document.getElementById('memberStatusSelect').value = m.status;
    document.getElementById('memberAvatarInput').value = m.avatar || '';

    openModal('teamModal');
  } catch (err) {
    showToast('Failed to load member details', 'error');
  }
}

async function handleTeamFormSubmit(e) {
  e.preventDefault();
  const id = document.getElementById('memberIdInput').value;
  const name = document.getElementById('memberNameInput').value.trim();
  const email = document.getElementById('memberEmailInput').value.trim();
  const role = document.getElementById('memberRoleInput').value.trim();
  const department = document.getElementById('memberDeptSelect').value;
  const phone = document.getElementById('memberPhoneInput').value.trim();
  const status = document.getElementById('memberStatusSelect').value;
  const avatar = document.getElementById('memberAvatarInput').value.trim();

  const payload = { name, email, role, department, phone, status, avatar };
  const method = id ? 'PUT' : 'POST';
  const url = id ? `/api/team/${id}` : '/api/team';

  try {
    const res = await fetch(url, {
      method,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const result = await res.json();

    if (result.success) {
      showToast(result.message || 'Team member saved', 'success');
      closeModal('teamModal');
      loadTeam();
    } else {
      showToast(result.error || 'Failed to save member', 'error');
    }
  } catch (err) {
    showToast('Network error while saving member', 'error');
  }
}

function confirmDeleteTeamMember(id, name) {
  if (confirm(`Are you sure you want to remove ${name} from the team?`)) {
    deleteTeamMember(id);
  }
}

async function deleteTeamMember(id) {
  try {
    const res = await fetch(`/api/team/${id}`, { method: 'DELETE' });
    const data = await res.json();
    if (data.success) {
      showToast('Team member removed', 'success');
      loadTeam();
    } else {
      showToast(data.error || 'Failed to remove member', 'error');
    }
  } catch (err) {
    showToast('Error removing member', 'error');
  }
}

// ==========================================================================
// AI ASSISTANT & CHATBOT CONTROLLER
// ==========================================================================
async function loadAIAssistant() {
  try {
    const res = await fetch('/api/ai/analyze');
    const data = await res.json();
    if (!data.success) return;

    // 1. Project Analysis
    const pa = data.project_analysis;
    const projectAlertBox = document.getElementById('aiProjectAlertsBox');
    if (projectAlertBox) {
      if (pa.delayed_projects.length === 0) {
        projectAlertBox.innerHTML = `
          <div style="padding: 16px; background: var(--success-bg); border-radius: var(--radius-md); color: var(--success); font-size: 0.88rem;">
            <strong>✓ All projects on track!</strong> No delayed projects detected in SQLite.
          </div>
        `;
      } else {
        projectAlertBox.innerHTML = pa.delayed_projects.map(p => `
          <div style="padding: 14px; background: var(--danger-bg); border: 1px solid rgba(239,68,68,0.25); border-radius: var(--radius-md); margin-bottom: 10px;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
              <strong style="color: var(--danger); font-size: 0.95rem;">${escapeHtml(p.name)}</strong>
              <span class="badge badge-urgent">Risk: ${p.risk_level}</span>
            </div>
            <div style="font-size: 0.82rem; margin-top: 6px; color: var(--text-primary);">
              Target deadline was <strong>${p.end_date}</strong> (${p.is_overdue ? `Overdue by ${Math.abs(p.days_remaining)} days` : 'Behind pace'}).
            </div>
            <div style="font-size: 0.78rem; color: var(--text-secondary); margin-top: 4px;">
              Progress: ${p.progress_pct}% completed • Health Score: <strong>${p.health_score}/100</strong>
            </div>
          </div>
        `).join('');
      }
    }

    // 2. Task Recommendations
    const recsBox = document.getElementById('aiTaskRecsBox');
    if (recsBox) {
      recsBox.innerHTML = data.task_recommendations.map((t, idx) => `
        <div style="padding: 12px; background: var(--bg-tertiary); border-radius: var(--radius-md); margin-bottom: 10px; border-left: 3px solid var(--primary);">
          <div style="display: flex; justify-content: space-between; align-items: center;">
            <strong style="font-size: 0.88rem; color: var(--text-primary);">${idx + 1}. ${escapeHtml(t.title)}</strong>
            <span class="badge badge-${t.priority.toLowerCase()}">Score: ${t.ai_score}</span>
          </div>
          <div style="font-size: 0.78rem; color: var(--primary); margin-top: 4px;">${escapeHtml(t.project_name)} • Assigned: ${escapeHtml(t.assignee_name)}</div>
          <div style="font-size: 0.76rem; color: var(--text-secondary); margin-top: 4px;">💡 ${escapeHtml(t.recommendation_reason)}</div>
        </div>
      `).join('');
    }

    // 3. Deadline Predictions
    const predBox = document.getElementById('aiDeadlinePredictionsBox');
    if (predBox) {
      predBox.innerHTML = data.deadline_predictions.map(dp => {
        const riskColor = dp.risk_status === 'High Risk' ? 'var(--danger)' : (dp.risk_status === 'Moderate Risk' ? 'var(--warning)' : 'var(--success)');
        return `
          <div style="padding: 12px; background: var(--bg-tertiary); border-radius: var(--radius-md); margin-bottom: 10px;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
              <strong style="font-size: 0.88rem; color: var(--text-primary);">${escapeHtml(dp.project_name)}</strong>
              <span style="font-size: 0.78rem; font-weight: 700; color: ${riskColor};">${dp.risk_status} (${dp.probability_miss_pct}% miss risk)</span>
            </div>
            <div style="font-size: 0.78rem; color: var(--text-secondary); margin-top: 4px;">
              Deadline: ${dp.end_date} • Estimated Completion: <strong>${dp.predicted_completion_date}</strong>
            </div>
            <div style="font-size: 0.76rem; color: var(--text-muted); margin-top: 4px;">
              ${escapeHtml(dp.ai_advice)}
            </div>
          </div>
        `;
      }).join('');
    }

    if (window.lucide) lucide.createIcons();

  } catch (err) {
    console.error('Error loading AI assistant data:', err);
  }
}

// Chatbot UI interactions
async function sendChatMessage(presetText) {
  const input = document.getElementById('chatInput');
  const message = presetText || input.value.trim();
  if (!message) return;

  if (!presetText) input.value = '';

  const messagesContainer = document.getElementById('chatMessagesBox');
  if (!messagesContainer) return;

  // Append user bubble
  appendChatBubble('user', message);
  messagesContainer.scrollTop = messagesContainer.scrollHeight;

  // Append typing indicator
  const typingId = 'typingIndicator_' + Date.now();
  const typingBubble = document.createElement('div');
  typingBubble.id = typingId;
  typingBubble.className = 'chat-msg bot';
  typingBubble.innerHTML = `
    <div class="chat-avatar"><i data-lucide="sparkles"></i></div>
    <div class="chat-bubble" style="color: var(--text-muted);">Thinking & inspecting software_management.db...</div>
  `;
  messagesContainer.appendChild(typingBubble);
  if (window.lucide) lucide.createIcons();
  messagesContainer.scrollTop = messagesContainer.scrollHeight;

  try {
    const res = await fetch('/api/ai/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message })
    });
    const data = await res.json();
    document.getElementById(typingId)?.remove();

    if (data.success) {
      appendChatBubble('bot', data.response.answer);
    } else {
      appendChatBubble('bot', '⚠️ Sorry, I encountered an issue retrieving real-time data from SQLite.');
    }
  } catch (err) {
    document.getElementById(typingId)?.remove();
    appendChatBubble('bot', '⚠️ Error contacting AI chat endpoint.');
  }

  messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function appendChatBubble(role, text) {
  const container = document.getElementById('chatMessagesBox');
  if (!container) return;

  const msg = document.createElement('div');
  msg.className = `chat-msg ${role}`;

  const icon = role === 'bot' ? '<i data-lucide="sparkles"></i>' : '<i data-lucide="user"></i>';

  msg.innerHTML = `
    <div class="chat-avatar">${icon}</div>
    <div class="chat-bubble">${renderMarkdown(text)}</div>
  `;
  container.appendChild(msg);
  if (window.lucide) lucide.createIcons();
}

function renderMarkdown(text) {
  if (!text) return '';
  let out = escapeHtml(text);
  // Headers
  out = out.replace(/^### (.*$)/gim, '<h3>$1</h3>');
  out = out.replace(/^## (.*$)/gim, '<h2>$1</h2>');
  // Bold
  out = out.replace(/\*\*(.*?)\*\*/gim, '<strong>$1</strong>');
  // Inline code
  out = out.replace(/`(.*?)`/gim, '<code>$1</code>');
  // Unordered list items
  out = out.replace(/^\- (.*$)/gim, '<li>$1</li>');
  out = out.replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>');
  // Line breaks
  out = out.replace(/\n/g, '<br>');
  return out;
}

// ==========================================================================
// REPORTS & ANALYTICS CONTROLLER
// ==========================================================================
let reportChartInstance = null;

async function loadReports() {
  try {
    const start_date = document.getElementById('reportStartDate')?.value || '';
    const end_date = document.getElementById('reportEndDate')?.value || '';

    const url = `/api/reports?start_date=${encodeURIComponent(start_date)}&end_date=${encodeURIComponent(end_date)}`;
    const res = await fetch(url);
    const data = await res.json();
    if (!data.success) return;

    // Render report table
    const tableBody = document.getElementById('delayedProjectsReportTable');
    if (tableBody) {
      if (data.delayed_projects.length === 0) {
        tableBody.innerHTML = `<tr><td colspan="7" style="text-align: center; padding: 24px; color: var(--text-muted);">No delayed projects found within this date range.</td></tr>`;
      } else {
        tableBody.innerHTML = data.delayed_projects.map(p => `
          <tr style="border-bottom: 1px solid var(--border-color);">
            <td style="padding: 12px 16px; font-weight: 600;">${escapeHtml(p.name)}</td>
            <td style="padding: 12px 16px;"><span class="badge badge-urgent">${p.priority}</span></td>
            <td style="padding: 12px 16px;">${p.end_date}</td>
            <td style="padding: 12px 16px; color: var(--danger); font-weight: 700;">${Math.abs(p.days_remaining)} days</td>
            <td style="padding: 12px 16px;">${p.completed_tasks}/${p.total_tasks} (${p.progress_pct}%)</td>
            <td style="padding: 12px 16px;"><span class="badge badge-urgent">${p.health_score}/100</span></td>
            <td style="padding: 12px 16px;">
              <button class="btn btn-secondary btn-sm" onclick="viewProjectDetails(${p.project_id})">Inspect</button>
            </td>
          </tr>
        `).join('');
      }
    }

    // Render Productivity Chart
    window.renderReportCharts = () => {
      renderTeamProductivityChart(data.team_productivity);
    };
    window.renderReportCharts();

  } catch (err) {
    console.error('Error loading reports:', err);
  }
}

function renderTeamProductivityChart(teamStats) {
  const ctx = document.getElementById('teamProductivityChart');
  if (!ctx || !teamStats) return;

  if (reportChartInstance) reportChartInstance.destroy();

  const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
  const textColor = isDark ? '#94a3b8' : '#475569';
  const gridColor = isDark ? 'rgba(255, 255, 255, 0.06)' : '#e2e8f0';

  reportChartInstance = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: teamStats.map(m => m.name),
      datasets: [
        {
          label: 'Completed Tasks',
          data: teamStats.map(m => m.completed_tasks),
          backgroundColor: '#10b981',
          borderRadius: 4
        },
        {
          label: 'Active Backlog',
          data: teamStats.map(m => m.active_tasks),
          backgroundColor: '#6366f1',
          borderRadius: 4
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { labels: { color: textColor, font: { family: 'Plus Jakarta Sans' } } }
      },
      scales: {
        x: { ticks: { color: textColor }, grid: { display: false } },
        y: { ticks: { color: textColor, stepSize: 1 }, grid: { color: gridColor } }
      }
    }
  });
}

function exportData(type) {
  window.location.href = `/api/export/${type}`;
  showToast(`Downloading ${type} CSV export...`, 'info');
}

// ==========================================================================
// Select Population Helpers
// ==========================================================================
async function populateTeamSelects(selectedLeadId = null, selectedMemberIds = []) {
  try {
    const res = await fetch('/api/team');
    const data = await res.json();
    if (!data.success) return;

    const leadSelect = document.getElementById('projectLeadSelect');
    if (leadSelect) {
      leadSelect.innerHTML = '<option value="">-- Select Project Lead --</option>' +
        data.team.map(m => `<option value="${m.id}" ${m.id === selectedLeadId ? 'selected' : ''}>${escapeHtml(m.name)} (${escapeHtml(m.role)})</option>`).join('');
    }

    const membersSelect = document.getElementById('projectMembersSelect');
    if (membersSelect) {
      membersSelect.innerHTML = data.team.map(m => `
        <option value="${m.id}" ${selectedMemberIds.includes(m.id) ? 'selected' : ''}>${escapeHtml(m.name)} - ${escapeHtml(m.department)}</option>
      `).join('');
    }
  } catch (e) {
    console.error(e);
  }
}

async function populateProjectAndTeamSelects(selectedProjectId = null, selectedAssigneeId = null) {
  try {
    const [pRes, tRes] = await Promise.all([fetch('/api/projects'), fetch('/api/team')]);
    const pData = await pRes.json();
    const tData = await tRes.json();

    const pSelect = document.getElementById('taskProjectSelect');
    if (pSelect && pData.success) {
      pSelect.innerHTML = '<option value="">-- Select Project --</option>' +
        pData.projects.map(p => `<option value="${p.id}" ${p.id === selectedProjectId ? 'selected' : ''}>${escapeHtml(p.name)}</option>`).join('');
    }

    const aSelect = document.getElementById('taskAssigneeSelect');
    if (aSelect && tData.success) {
      aSelect.innerHTML = '<option value="">-- Unassigned --</option>' +
        tData.team.map(m => `<option value="${m.id}" ${m.id === selectedAssigneeId ? 'selected' : ''}>${escapeHtml(m.name)} (${escapeHtml(m.role)})</option>`).join('');
    }
  } catch (e) {
    console.error(e);
  }
}

// ==========================================================================
// Utilities
// ==========================================================================
function escapeHtml(text) {
  if (!text) return '';
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

function formatTimeAgo(dateString) {
  if (!dateString) return '';
  const d = new Date(dateString);
  const now = new Date();
  const diffSec = Math.floor((now - d) / 1000);

  if (diffSec < 60) return 'Just now';
  if (diffSec < 3600) return `${Math.floor(diffSec / 60)}m ago`;
  if (diffSec < 86400) return `${Math.floor(diffSec / 3600)}h ago`;
  return `${Math.floor(diffSec / 86400)}d ago`;
}

// ==========================================================================
// Lifecycle Initialization
// ==========================================================================
document.addEventListener('DOMContentLoaded', () => {
  initTheme();
  if (window.lucide) lucide.createIcons();

  // Route-specific loader
  const page = document.body.getAttribute('data-page');
  if (page === 'dashboard') loadDashboard();
  if (page === 'projects') loadProjects();
  if (page === 'tasks') loadTasks();
  if (page === 'team') loadTeam();
  if (page === 'ai-assistant') loadAIAssistant();
  if (page === 'analytics') loadReports();
});
