/**
 * ExpenseAI - Frontend Controller & Visualization Engine
 * Minor Project: Automated Expense Categorization & Spending Analysis Platform
 * Authors: Pratyush (B.Com) & Komalpreet Kaur (BCA) - PCTE
 */

// Category Palette for visual consistency
const CATEGORY_COLORS = {
  "Food & Dining": "#f97316",
  "Groceries & Essentials": "#10b981",
  "Shopping & E-Commerce": "#ec4899",
  "Travel & Commute": "#3b82f6",
  "Utilities & Bills": "#eab308",
  "Entertainment & Subscriptions": "#8b5cf6",
  "Healthcare & Medical": "#14b8a6",
  "Investments & Savings": "#6366f1",
  "Income & Salary": "#22c55e",
  "Miscellaneous & Transfers": "#64748b"
};

const CATEGORY_ICONS = {
  "Food & Dining": "fa-utensils",
  "Groceries & Essentials": "fa-basket-shopping",
  "Shopping & E-Commerce": "fa-bag-shopping",
  "Travel & Commute": "fa-car",
  "Utilities & Bills": "fa-lightbulb",
  "Entertainment & Subscriptions": "fa-film",
  "Healthcare & Medical": "fa-heart-pulse",
  "Investments & Savings": "fa-chart-line",
  "Income & Salary": "fa-money-bill-trend-up",
  "Miscellaneous & Transfers": "fa-arrows-rotate"
};

// Global State
let allCategories = [];
let categoryChartInstance = null;
let trendChartInstance = null;
let merchantChartInstance = null;
let selectedFile = null;
let debounceTimer = null;

// Currency Formatter
const formatINR = (amt) => {
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 2
  }).format(amt);
};

// Toast Notifications
function showToast(message, type = 'info') {
  const container = document.getElementById('toast-container');
  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  
  let icon = 'fa-info-circle';
  if (type === 'success') icon = 'fa-circle-check';
  if (type === 'error') icon = 'fa-circle-exclamation';

  toast.innerHTML = `<i class="fa-solid ${icon}"></i> <span>${message}</span>`;
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(20px)';
    toast.style.transition = 'all 0.3s ease';
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

// Modal Controllers
function openModal(id) {
  const modal = document.getElementById(id);
  if (modal) modal.classList.add('active');
}

function closeModal(id) {
  const modal = document.getElementById(id);
  if (modal) modal.classList.remove('active');
}

// Initialize Application
document.addEventListener('DOMContentLoaded', () => {
  setupEventListeners();
  setupDragAndDrop();
  initCharts();
  loadCategories();
  refreshDashboard();
  
  // Set default date in Add modal to today
  const addDateInput = document.getElementById('add-date');
  if (addDateInput) {
    addDateInput.value = new Date().toISOString().split('T')[0];
  }
});

// Setup Event Listeners
function setupEventListeners() {
  // Modal Open Buttons
  document.getElementById('btn-open-add').addEventListener('click', () => openModal('modal-add-txn'));
  document.getElementById('btn-open-upload').addEventListener('click', () => openModal('modal-upload'));
  document.getElementById('btn-open-budget').addEventListener('click', () => openModal('modal-budget'));
  document.getElementById('btn-edit-budgets').addEventListener('click', () => openModal('modal-budget'));
  document.getElementById('btn-open-about').addEventListener('click', () => openModal('modal-about'));

  // Hero banner buttons
  document.getElementById('hero-load-demo').addEventListener('click', () => loadPresetDataset('all'));
  document.getElementById('hero-upload-file').addEventListener('click', () => openModal('modal-upload'));
  document.getElementById('btn-quick-sample').addEventListener('click', () => loadPresetDataset('all'));

  // Close modals
  document.querySelectorAll('[data-close]').forEach(btn => {
    btn.addEventListener('click', () => closeModal(btn.getAttribute('data-close')));
  });

  // Modal backdrop click
  document.querySelectorAll('.modal-backdrop').forEach(modal => {
    modal.addEventListener('click', (e) => {
      if (e.target === modal) modal.classList.remove('active');
    });
  });

  // Escape key closes modals
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      document.querySelectorAll('.modal-backdrop.active').forEach(m => m.classList.remove('active'));
    }
  });

  // Filters & Search
  document.getElementById('filter-search').addEventListener('input', () => {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(loadTransactions, 300);
  });
  document.getElementById('filter-category').addEventListener('change', loadTransactions);
  document.getElementById('filter-type').addEventListener('change', loadTransactions);
  document.getElementById('filter-account').addEventListener('change', loadTransactions);
  document.getElementById('btn-reset-filters').addEventListener('click', () => {
    document.getElementById('filter-search').value = '';
    document.getElementById('filter-category').value = 'All';
    document.getElementById('filter-type').value = 'ALL';
    document.getElementById('filter-account').value = 'All';
    loadTransactions();
  });

  // Add Transaction Form
  document.getElementById('form-add-txn').addEventListener('submit', handleAddTransaction);
  document.getElementById('add-desc').addEventListener('input', handleDescriptionInput);

  // Preset Loaders in Upload Modal
  document.querySelectorAll('.load-preset-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const preset = btn.getAttribute('data-preset');
      loadPresetDataset(preset);
      closeModal('modal-upload');
    });
  });

  // Clear All Data
  document.getElementById('btn-clear-all').addEventListener('click', handleClearAll);

  // Export CSV
  document.getElementById('btn-export-csv').addEventListener('click', () => {
    window.location.href = '/api/export';
    showToast('Downloading expense ledger CSV...', 'info');
  });
}

// Drag & Drop Statement File Upload
function setupDragAndDrop() {
  const dropzone = document.getElementById('dropzone');
  const fileInput = document.getElementById('file-input');
  const browseBtn = document.getElementById('btn-browse-file');
  const submitBtn = document.getElementById('btn-submit-upload');
  const previewDiv = document.getElementById('file-selected-name');

  browseBtn.addEventListener('click', () => fileInput.click());

  fileInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
      handleFileSelected(e.target.files[0]);
    }
  });

  dropzone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropzone.classList.add('drag-over');
  });

  dropzone.addEventListener('dragleave', () => dropzone.classList.remove('drag-over'));

  dropzone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropzone.classList.remove('drag-over');
    if (e.dataTransfer.files.length > 0) {
      handleFileSelected(e.dataTransfer.files[0]);
    }
  });

  function handleFileSelected(file) {
    selectedFile = file;
    previewDiv.style.display = 'block';
    previewDiv.innerHTML = `<i class="fa-solid fa-file-csv"></i> ${file.name} (${(file.size / 1024).toFixed(1)} KB)`;
    submitBtn.removeAttribute('disabled');
  }

  submitBtn.addEventListener('click', async () => {
    if (!selectedFile) return;
    const accountLabel = document.getElementById('upload-account-label').value || 'Bank Statement';
    
    submitBtn.setAttribute('disabled', 'true');
    submitBtn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Processing & Categorizing...`;

    const formData = new FormData();
    formData.append('file', selectedFile);
    formData.append('account_name', accountLabel);

    try {
      const res = await fetch('/api/upload', {
        method: 'POST',
        body: formData
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Upload failed');

      showToast(data.message, 'success');
      closeModal('modal-upload');
      selectedFile = null;
      fileInput.value = '';
      previewDiv.style.display = 'none';
      submitBtn.innerHTML = `<i class="fa-solid fa-play"></i> Process & Categorize Statement`;
      refreshDashboard();
    } catch (err) {
      showToast(err.message, 'error');
      submitBtn.removeAttribute('disabled');
      submitBtn.innerHTML = `<i class="fa-solid fa-play"></i> Process & Categorize Statement`;
    }
  });
}

// Load Categories
async function loadCategories() {
  try {
    const res = await fetch('/api/categories');
    const data = await res.json();
    allCategories = data.categories;

    // Populate filter dropdown
    const filterCat = document.getElementById('filter-category');
    filterCat.innerHTML = `<option value="All">All Categories</option>`;
    
    // Populate add transaction category dropdown
    const addCat = document.getElementById('add-category');
    addCat.innerHTML = `<option value="">🤖 Auto-Detect (AI Recommendation)</option>`;

    allCategories.forEach(cat => {
      filterCat.innerHTML += `<option value="${cat}">${cat}</option>`;
      addCat.innerHTML += `<option value="${cat}">${cat}</option>`;
    });

    // Populate Budget Modal Inputs
    loadBudgetsModal();
  } catch (err) {
    console.error('Failed to load categories', err);
  }
}

// Live AI Prediction as user types merchant in Add form
async function handleDescriptionInput(e) {
  const text = e.target.value.trim();
  const suggestionChip = document.getElementById('add-ai-suggestion');
  const suggestionText = document.getElementById('suggestion-text');
  
  if (text.length < 3) {
    suggestionChip.style.display = 'none';
    return;
  }

  const amt = parseFloat(document.getElementById('add-amount').value) || 0;
  const type = document.getElementById('add-type').value || 'DEBIT';

  clearTimeout(debounceTimer);
  debounceTimer = setTimeout(async () => {
    try {
      const res = await fetch(`/api/predict?text=${encodeURIComponent(text)}&amount=${amt}&type=${type}`);
      const data = await res.json();
      
      suggestionChip.style.display = 'flex';
      suggestionText.innerHTML = `AI Recommendation: <strong>${data.category}</strong> (${Math.round(data.confidence * 100)}% match) for <em>"${data.clean_merchant}"</em>`;
    } catch (err) {
      suggestionChip.style.display = 'none';
    }
  }, 250);
}

// Add Transaction Form Handler
async function handleAddTransaction(e) {
  e.preventDefault();
  const desc = document.getElementById('add-desc').value.trim();
  const amt = parseFloat(document.getElementById('add-amount').value);
  const type = document.getElementById('add-type').value;
  const date = document.getElementById('add-date').value;
  const cat = document.getElementById('add-category').value || null;
  const account = document.getElementById('add-account').value.trim() || 'Manual Entry';

  if (!desc || isNaN(amt) || amt <= 0 || !date) {
    showToast('Please fill all required fields correctly.', 'error');
    return;
  }

  try {
    const res = await fetch('/api/transactions', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        description: desc,
        amount: amt,
        type: type,
        date: date,
        category: cat,
        account: account
      })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Failed to save transaction');

    showToast(`Categorized as "${data.category}" successfully!`, 'success');
    closeModal('modal-add-txn');
    document.getElementById('form-add-txn').reset();
    document.getElementById('add-date').value = new Date().toISOString().split('T')[0];
    document.getElementById('add-ai-suggestion').style.display = 'none';
    refreshDashboard();
  } catch (err) {
    showToast(err.message, 'error');
  }
}

// Load Preset Dataset (One click demo)
async function loadPresetDataset(preset) {
  try {
    showToast(`Loading demo statements...`, 'info');
    const res = await fetch(`/api/load-sample/${preset}`, { method: 'POST' });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Failed to load demo data');

    showToast(data.message, 'success');
    refreshDashboard();
  } catch (err) {
    showToast(err.message, 'error');
  }
}

// Clear All Data
async function handleClearAll() {
  if (!confirm('Are you sure you want to clear all transactions? You can easily reload sample demo data anytime.')) {
    return;
  }
  try {
    const res = await fetch('/api/transactions', { method: 'DELETE' });
    const data = await res.json();
    showToast('All transactions cleared.', 'info');
    refreshDashboard();
  } catch (err) {
    showToast('Failed to clear data.', 'error');
  }
}

// Master Refresh Function
function refreshDashboard() {
  loadAnalytics();
  loadTransactions();
}

// Initialize Charts
function initCharts() {
  // 1. Category Doughnut Chart
  const ctxCat = document.getElementById('categoryChart').getContext('2d');
  categoryChartInstance = new Chart(ctxCat, {
    type: 'doughnut',
    data: {
      labels: [],
      datasets: [{
        data: [],
        backgroundColor: [],
        borderWidth: 2,
        borderColor: '#111827'
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: '72%',
      plugins: {
        legend: {
          display: true,
          position: 'bottom',
          labels: {
            boxWidth: 10,
            padding: 12,
            font: { family: 'Plus Jakarta Sans', size: 11 },
            color: '#94a3b8'
          }
        },
        tooltip: {
          callbacks: {
            label: (ctx) => ` ${ctx.label}: ${formatINR(ctx.raw)}`
          }
        }
      }
    }
  });

  // 2. Trend Bar Chart
  const ctxTrend = document.getElementById('trendChart').getContext('2d');
  trendChartInstance = new Chart(ctxTrend, {
    type: 'bar',
    data: {
      labels: [],
      datasets: [
        {
          label: 'Income',
          data: [],
          backgroundColor: 'rgba(16, 185, 129, 0.8)',
          borderRadius: 6
        },
        {
          label: 'Expense',
          data: [],
          backgroundColor: 'rgba(244, 63, 94, 0.8)',
          borderRadius: 6
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: (ctx) => ` ${ctx.dataset.label}: ${formatINR(ctx.raw)}`
          }
        }
      },
      scales: {
        x: {
          grid: { display: false },
          ticks: { color: '#94a3b8', font: { family: 'Plus Jakarta Sans', size: 11 } }
        },
        y: {
          grid: { color: 'rgba(255, 255, 255, 0.05)' },
          ticks: {
            color: '#94a3b8',
            font: { family: 'Plus Jakarta Sans', size: 10 },
            callback: (val) => `₹${val >= 1000 ? (val/1000).toFixed(0) + 'k' : val}`
          }
        }
      }
    }
  });

  // 3. Top Merchant Chart
  const ctxMerchant = document.getElementById('merchantChart').getContext('2d');
  merchantChartInstance = new Chart(ctxMerchant, {
    type: 'bar',
    data: {
      labels: [],
      datasets: [{
        label: 'Spent',
        data: [],
        backgroundColor: '#818cf8',
        borderRadius: 6
      }]
    },
    options: {
      indexAxis: 'y',
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: (ctx) => ` Spent: ${formatINR(ctx.raw)}`
          }
        }
      },
      scales: {
        x: {
          grid: { color: 'rgba(255, 255, 255, 0.05)' },
          ticks: {
            color: '#94a3b8',
            font: { family: 'Plus Jakarta Sans', size: 10 },
            callback: (val) => `₹${val >= 1000 ? (val/1000).toFixed(0) + 'k' : val}`
          }
        },
        y: {
          grid: { display: false },
          ticks: { color: '#f8fafc', font: { family: 'Plus Jakarta Sans', size: 11, weight: '500' } }
        }
      }
    }
  });
}

// Load Analytics & Update Visuals
async function loadAnalytics() {
  try {
    const res = await fetch('/api/analytics');
    const data = await res.json();
    
    const kpis = data.kpis;
    const banner = document.getElementById('empty-state-banner');
    
    // Toggle empty banner if 0 transactions
    if (kpis.total_txns === 0) {
      banner.style.display = 'flex';
    } else {
      banner.style.display = 'none';
    }

    // Update KPIs
    document.getElementById('kpi-income').textContent = formatINR(kpis.total_income);
    document.getElementById('kpi-expense').textContent = formatINR(kpis.total_expense);
    document.getElementById('kpi-savings').textContent = formatINR(kpis.net_savings);
    document.getElementById('kpi-savings-rate').textContent = `${kpis.savings_rate}% Savings Rate`;
    document.getElementById('kpi-count').textContent = kpis.total_txns;

    // Top Category KPI
    const topCat = data.category_breakdown.length > 0 ? data.category_breakdown[0].category : 'None';
    document.getElementById('kpi-top-category').textContent = `Top: ${topCat}`;
    document.getElementById('category-count-badge').textContent = `${data.category_breakdown.length} Categories`;

    // Update Doughnut Chart
    if (categoryChartInstance) {
      categoryChartInstance.data.labels = data.category_breakdown.map(c => c.category);
      categoryChartInstance.data.datasets[0].data = data.category_breakdown.map(c => c.total_amount);
      categoryChartInstance.data.datasets[0].backgroundColor = data.category_breakdown.map(c => CATEGORY_COLORS[c.category] || '#64748b');
      categoryChartInstance.update();
    }

    // Update Trend Chart
    if (trendChartInstance) {
      trendChartInstance.data.labels = data.monthly_trend.map(t => t.month);
      trendChartInstance.data.datasets[0].data = data.monthly_trend.map(t => t.income);
      trendChartInstance.data.datasets[1].data = data.monthly_trend.map(t => t.expense);
      trendChartInstance.update();
    }

    // Update Top Merchants Chart
    if (merchantChartInstance) {
      merchantChartInstance.data.labels = data.top_merchants.map(m => m.merchant);
      merchantChartInstance.data.datasets[0].data = data.top_merchants.map(m => m.total_spent);
      merchantChartInstance.update();
    }

    // Render Budget Guardrails
    renderBudgetBars(data.budget_analysis);

  } catch (err) {
    console.error('Failed to load analytics', err);
  }
}

// Render Budget Guardrail Bars
function renderBudgetBars(budgets) {
  const container = document.getElementById('budget-bars-container');
  if (!budgets || budgets.length === 0) {
    container.innerHTML = `<div class="text-muted" style="grid-column: 1/-1; text-align: center; padding: 1.5rem;">No budget data available.</div>`;
    return;
  }

  container.innerHTML = budgets.map(b => {
    let statusClass = 'status-safe';
    let progressClass = 'progress-safe';
    let label = 'Safe';

    if (b.status === 'EXCEEDED') {
      statusClass = 'status-exceeded';
      progressClass = 'progress-exceeded';
      label = 'Exceeded';
    } else if (b.status === 'WARNING') {
      statusClass = 'status-warning';
      progressClass = 'progress-warning';
      label = 'Warning';
    }

    const clampedPct = Math.min(b.percentage, 100);
    const catIcon = CATEGORY_ICONS[b.category] || 'fa-tag';

    return `
      <div class="budget-bar-card">
        <div class="budget-bar-top">
          <span class="budget-cat-name">
            <i class="fa-solid ${catIcon}" style="color: ${CATEGORY_COLORS[b.category] || '#818cf8'}"></i>
            ${b.category}
          </span>
          <span class="budget-status-tag ${statusClass}">${label} (${b.percentage}%)</span>
        </div>
        <div class="progress-track">
          <div class="progress-fill ${progressClass}" style="width: ${clampedPct}%;"></div>
        </div>
        <div class="budget-bar-bottom">
          <span>Spent: <strong>${formatINR(b.spent)}</strong></span>
          <span>Limit: <strong>${formatINR(b.monthly_limit)}</strong></span>
        </div>
      </div>
    `;
  }).join('');
}

// Load Budgets in Modal for Editing
async function loadBudgetsModal() {
  try {
    const res = await fetch('/api/budgets');
    const data = await res.json();
    const container = document.getElementById('budget-inputs-list');
    
    container.innerHTML = data.budgets.map(b => `
      <div class="budget-input-item">
        <label><i class="fa-solid ${CATEGORY_ICONS[b.category] || 'fa-tag'}"></i> ${b.category}</label>
        <input type="number" step="100" min="0" value="${b.monthly_limit}" data-category="${b.category}" class="budget-limit-input">
      </div>
    `).join('');

    // Attach change handlers
    document.querySelectorAll('.budget-limit-input').forEach(input => {
      input.addEventListener('change', async (e) => {
        const cat = e.target.getAttribute('data-category');
        const limit = parseFloat(e.target.value);
        if (isNaN(limit) || limit < 0) return;

        try {
          await fetch('/api/budgets', {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ category: cat, monthly_limit: limit })
          });
          showToast(`Budget for "${cat}" updated to ${formatINR(limit)}`, 'success');
          loadAnalytics();
        } catch (err) {
          showToast('Failed to update budget', 'error');
        }
      });
    });
  } catch (err) {
    console.error('Failed to load budgets', err);
  }
}

// Load Transactions Table
async function loadTransactions() {
  const search = document.getElementById('filter-search').value.trim();
  const category = document.getElementById('filter-category').value;
  const type = document.getElementById('filter-type').value;
  const account = document.getElementById('filter-account').value;

  let url = `/api/transactions?limit=150`;
  if (search) url += `&search=${encodeURIComponent(search)}`;
  if (category && category !== 'All') url += `&category=${encodeURIComponent(category)}`;
  if (type && type !== 'ALL') url += `&txn_type=${encodeURIComponent(type)}`;
  if (account && account !== 'All') url += `&account=${encodeURIComponent(account)}`;

  try {
    const res = await fetch(url);
    const data = await res.json();
    const tbody = document.getElementById('transactions-tbody');
    const emptyNotice = document.getElementById('table-empty-notice');

    // Populate Account Filter dynamically if needed
    populateAccountFilter(data.transactions);

    if (data.transactions.length === 0) {
      tbody.innerHTML = '';
      emptyNotice.style.display = 'block';
      return;
    }

    emptyNotice.style.display = 'none';
    tbody.innerHTML = data.transactions.map(t => {
      const isDebit = t.type === 'DEBIT';
      const amtClass = isDebit ? 'amount-debit' : 'amount-credit';
      const amtPrefix = isDebit ? '- ' : '+ ';
      const catColor = CATEGORY_COLORS[t.category] || '#64748b';
      const catIcon = CATEGORY_ICONS[t.category] || 'fa-tag';
      const confidencePercent = Math.round((t.confidence || 1.0) * 100);

      // Category options for inline override
      const categoryOptions = allCategories.map(c => 
        `<option value="${c}" ${c === t.category ? 'selected' : ''}>${c}</option>`
      ).join('');

      return `
        <tr data-id="${t.id}">
          <td><span style="font-size: 0.8rem; color: #94a3b8;">${t.date}</span></td>
          <td>
            <div class="merchant-cell">
              <div class="merchant-icon" style="color: ${catColor};">
                <i class="fa-solid ${catIcon}"></i>
              </div>
              <span>${t.clean_merchant}</span>
            </div>
          </td>
          <td>
            <div class="raw-narration-cell" title="${t.raw_description}">
              ${t.raw_description}
            </div>
          </td>
          <td>
            <select class="table-select-cat" data-txn-id="${t.id}" title="Reassign category (AI remembers for future)">
              ${categoryOptions}
            </select>
          </td>
          <td>
            <span class="confidence-badge" title="Model confidence score">
              ${confidencePercent}%
            </span>
          </td>
          <td>
            <span class="amount-cell ${amtClass}">
              ${amtPrefix}${formatINR(t.amount)}
            </span>
          </td>
          <td>
            <span style="font-size: 0.75rem; color: #94a3b8;">
              <i class="fa-solid fa-building-columns"></i> ${t.account}
            </span>
          </td>
          <td>
            <button class="btn-action-delete" data-delete-id="${t.id}" title="Delete transaction">
              <i class="fa-solid fa-trash-can"></i>
            </button>
          </td>
        </tr>
      `;
    }).join('');

    // Attach Inline Category Reassignment Listeners (Active Learning)
    document.querySelectorAll('.table-select-cat').forEach(select => {
      select.addEventListener('change', async (e) => {
        const txnId = e.target.getAttribute('data-txn-id');
        const newCategory = e.target.value;
        try {
          const updateRes = await fetch(`/api/transactions/${txnId}/category`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ category: newCategory, apply_to_future: true })
          });
          if (!updateRes.ok) throw new Error('Failed to update category');
          
          showToast(`Reassigned to "${newCategory}". Active learning updated!`, 'success');
          refreshDashboard();
        } catch (err) {
          showToast('Failed to reassign category', 'error');
        }
      });
    });

    // Attach Delete Listeners
    document.querySelectorAll('.btn-action-delete').forEach(btn => {
      btn.addEventListener('click', async (e) => {
        const txnId = btn.getAttribute('data-delete-id');
        try {
          const delRes = await fetch(`/api/transactions/${txnId}`, { method: 'DELETE' });
          if (!delRes.ok) throw new Error('Failed to delete');
          showToast('Transaction removed', 'info');
          refreshDashboard();
        } catch (err) {
          showToast('Failed to delete transaction', 'error');
        }
      });
    });

  } catch (err) {
    console.error('Failed to load transactions', err);
  }
}

// Populate Account dropdown filter based on active transactions
function populateAccountFilter(transactions) {
  const accountSelect = document.getElementById('filter-account');
  const currentVal = accountSelect.value;
  const accounts = [...new Set(transactions.map(t => t.account).filter(Boolean))];

  if (accountSelect.options.length <= 1 + accounts.length) {
    accounts.forEach(acc => {
      if (!Array.from(accountSelect.options).some(o => o.value === acc)) {
        const opt = document.createElement('option');
        opt.value = acc;
        opt.textContent = acc;
        accountSelect.appendChild(opt);
      }
    });
  }
  accountSelect.value = currentVal;
}
