// GovTracker2 Python Migration by Replit Agent - Task Reports Management

let reportsData = [];

// Load reports data
async function loadReportsData() {
    console.log('Loading reports data...');
    try {
        const response = await fetch('/api/task-reports');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        reportsData = await response.json();
        updateReportsGrid();
        
    } catch (error) {
        console.error('Error loading reports data:', error);
        showToast('Failed to load reports data', 'error');
    }
}

// Update reports grid
function updateReportsGrid() {
    const grid = document.getElementById('reports-grid');
    if (!grid) return;
    
    grid.innerHTML = '';
    
    if (reportsData.length === 0) {
        grid.innerHTML = `
            <div class="text-center py-12">
                <i class="fas fa-clipboard-list text-6xl text-gray-300 dark:text-gray-600 mb-4"></i>
                <h3 class="text-xl font-medium text-gray-900 dark:text-white mb-2">No Task Reports</h3>
                <p class="text-gray-500 dark:text-gray-400 mb-6">Task completion reports will appear here</p>
                <button onclick="showAddReportModal()" class="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg">
                    <i class="fas fa-plus mr-2"></i>Create First Report
                </button>
            </div>
        `;
        return;
    }
    
    reportsData.forEach(report => {
        const reportCard = createReportCard(report);
        grid.appendChild(reportCard);
    });
}

// Create report card
function createReportCard(report) {
    const card = document.createElement('div');
    card.className = 'bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6 hover:shadow-xl transition-shadow border border-gray-200 dark:border-gray-700';
    
    const statusColor = getStatusColor(report.status);
    const completionRate = report.task_count > 0 ? Math.round((report.approved_tasks / report.task_count) * 100) : 0;
    
    card.innerHTML = `
        <div class="flex items-start justify-between mb-4">
            <div>
                <h3 class="font-bold text-gray-900 dark:text-white mb-1">${report.title}</h3>
                <p class="text-sm text-gray-500 dark:text-gray-400">by ${report.author_name}</p>
                <p class="text-xs text-gray-400 dark:text-gray-500">${new Date(report.report_date).toLocaleDateString()}</p>
            </div>
            <div class="flex space-x-2">
                <span class="px-2 py-1 rounded-full text-xs font-medium ${statusColor}">
                    ${report.status.charAt(0).toUpperCase() + report.status.slice(1)}
                </span>
                <button onclick="editReport(${report.id})" class="text-blue-600 hover:text-blue-800 dark:text-blue-400">
                    <i class="fas fa-edit"></i>
                </button>
                <button onclick="deleteReport(${report.id})" class="text-red-600 hover:text-red-800 dark:text-red-400">
                    <i class="fas fa-trash"></i>
                </button>
            </div>
        </div>
        
        <div class="space-y-3">
            <div class="grid grid-cols-3 gap-4">
                <div class="text-center">
                    <p class="text-2xl font-bold text-gray-900 dark:text-white">${report.task_count}</p>
                    <p class="text-xs text-gray-500 dark:text-gray-400">Total Tasks</p>
                </div>
                <div class="text-center">
                    <p class="text-2xl font-bold text-green-600 dark:text-green-400">${report.approved_tasks}</p>
                    <p class="text-xs text-gray-500 dark:text-gray-400">Approved</p>
                </div>
                <div class="text-center">
                    <p class="text-2xl font-bold text-red-600 dark:text-red-400">${report.rejected_tasks}</p>
                    <p class="text-xs text-gray-500 dark:text-gray-400">Rejected</p>
                </div>
            </div>
            
            <div class="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                <div class="bg-green-600 h-2 rounded-full" style="width: ${completionRate}%"></div>
            </div>
            <p class="text-center text-sm text-gray-600 dark:text-gray-400">${completionRate}% completion rate</p>
            
            ${report.description ? `
                <div class="mt-4 pt-4 border-t border-gray-200 dark:border-gray-600">
                    <p class="text-sm text-gray-600 dark:text-gray-400">${report.description}</p>
                </div>
            ` : ''}
        </div>
    `;
    
    return card;
}

// Get status color
function getStatusColor(status) {
    const colors = {
        'pending': 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300',
        'approved': 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300',
        'rejected': 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300',
        'under_review': 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300'
    };
    return colors[status] || colors['pending'];
}

// Show add report modal
function showAddReportModal() {
    showToast('Report creation coming soon', 'info');
}

// Edit report
function editReport(reportId) {
    showToast('Edit functionality coming soon', 'info');
}

// Delete report
async function deleteReport(reportId) {
    if (!confirm('Are you sure you want to delete this report? This action cannot be undone.')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/task-reports/${reportId}`, {
            method: 'DELETE'
        });
        
        if (!response.ok) {
            throw new Error('Failed to delete report');
        }
        
        reportsData = reportsData.filter(r => r.id !== reportId);
        updateReportsGrid();
        showToast('Report deleted successfully', 'success');
        
    } catch (error) {
        console.error('Error deleting report:', error);
        showToast('Failed to delete report', 'error');
    }
}

// Refresh reports
function refreshReports() {
    loadReportsData();
}

// Make functions available globally
window.loadReportsData = loadReportsData;
window.showAddReportModal = showAddReportModal;
window.editReport = editReport;
window.deleteReport = deleteReport;
window.refreshReports = refreshReports;