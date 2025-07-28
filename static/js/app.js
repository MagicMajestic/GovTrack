// GovTracker2 Python Migration by Replit Agent

// Global state
let currentSection = 'dashboard';
let dashboardData = null;
let isDarkMode = localStorage.getItem('darkMode') === 'true';
let charts = {};

// Initialize app
document.addEventListener('DOMContentLoaded', function() {
    initializeTheme();
    loadDashboardData();
    setupEventListeners();
});

// Theme management
function initializeTheme() {
    if (isDarkMode) {
        document.documentElement.classList.add('dark');
    } else {
        document.documentElement.classList.remove('dark');
    }
}

function toggleTheme() {
    isDarkMode = !isDarkMode;
    localStorage.setItem('darkMode', isDarkMode.toString());
    
    if (isDarkMode) {
        document.documentElement.classList.add('dark');
    } else {
        document.documentElement.classList.remove('dark');
    }
    
    // Update charts for new theme
    updateChartsTheme();
}

// Navigation
function showSection(sectionName) {
    // Hide all sections
    document.querySelectorAll('.section-content').forEach(section => {
        section.classList.add('hidden');
    });
    
    // Show selected section
    const targetSection = document.getElementById(`${sectionName}-section`);
    if (targetSection) {
        targetSection.classList.remove('hidden');
        targetSection.classList.add('animate-fade-in');
    }
    
    // Update navigation active state
    document.querySelectorAll('.nav-link').forEach(link => {
        link.classList.remove('active');
        link.classList.add('border-transparent', 'text-gray-500', 'dark:text-gray-300');
        link.classList.remove('border-blue-500', 'text-gray-900', 'dark:text-white');
    });
    
    // Set active navigation item
    const activeLink = document.querySelector(`[onclick="showSection('${sectionName}')"]`);
    if (activeLink) {
        activeLink.classList.add('active');
        activeLink.classList.remove('border-transparent', 'text-gray-500', 'dark:text-gray-300');
        activeLink.classList.add('border-blue-500', 'text-gray-900', 'dark:text-white');
    }
    
    currentSection = sectionName;
    
    // Load section-specific data and handle auto-refresh
    loadSectionData(sectionName);
    
    // Stop auto-refresh for previous sections
    if (window.cleanupCuratorsSection && currentSection === 'curators') {
        window.cleanupCuratorsSection();
    }
    if (window.cleanupActivitiesSection && currentSection === 'activities') {
        window.cleanupActivitiesSection();
    }
    
    // Start auto-refresh for new section
    if (sectionName === 'curators' && window.initializeCuratorsSection) {
        window.initializeCuratorsSection();
    }
    if (sectionName === 'activities' && window.initializeActivitiesSection) {
        window.initializeActivitiesSection();
    }
}

// Data loading
async function loadDashboardData() {
    try {
        const response = await fetch('/api/dashboard/stats');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        dashboardData = await response.json();
        updateDashboardStats();
        
    } catch (error) {
        console.error('Error loading dashboard data:', error);
        // Set default values instead of infinite loading
        document.getElementById('total-curators').textContent = '0';
        document.getElementById('active-servers').textContent = '0';
        document.getElementById('total-activities').textContent = '0';
        document.getElementById('avg-response').textContent = '0s';
        
        // Hide charts section
        const chartsSection = document.querySelector('.grid.grid-cols-1.lg\\:grid-cols-2');
        if (chartsSection) chartsSection.style.display = 'none';
    }
}

function updateDashboardStats() {
    if (!dashboardData) return;
    
    // Update basic stats only
    const totalCuratorsEl = document.getElementById('total-curators');
    const activeServersEl = document.getElementById('active-servers');
    const totalActivitiesEl = document.getElementById('total-activities');
    const avgResponseEl = document.getElementById('avg-response');
    
    if (totalCuratorsEl) totalCuratorsEl.textContent = dashboardData.totalCurators || 0;
    if (activeServersEl) activeServersEl.textContent = dashboardData.activeServers || 0;
    if (totalActivitiesEl) totalActivitiesEl.textContent = dashboardData.totalActivities || 0;
    if (avgResponseEl) avgResponseEl.textContent = `${dashboardData.averageResponseTime || 0}s`;
}



function updateDailyChart() {
    const ctx = document.getElementById('daily-chart');
    if (!ctx || !dashboardData.dailyStats) return;
    
    // Destroy existing chart
    if (charts.dailyChart) {
        charts.dailyChart.destroy();
    }
    
    const labels = dashboardData.dailyStats.map(stat => {
        const date = new Date(stat.date);
        return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    });
    
    const data = dashboardData.dailyStats.map(stat => stat.total || 0);
    
    charts.dailyChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Daily Activities',
                data: data,
                borderColor: '#3B82F6',
                backgroundColor: 'rgba(59, 130, 246, 0.1)',
                borderWidth: 3,
                fill: true,
                tension: 0.4,
                pointBackgroundColor: '#3B82F6',
                pointBorderColor: '#ffffff',
                pointBorderWidth: 2,
                pointRadius: 6,
                pointHoverRadius: 8
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                x: {
                    grid: {
                        display: false
                    },
                    ticks: {
                        color: isDarkMode ? '#9CA3AF' : '#6B7280'
                    }
                },
                y: {
                    beginAtZero: true,
                    grid: {
                        color: isDarkMode ? '#374151' : '#E5E7EB'
                    },
                    ticks: {
                        color: isDarkMode ? '#9CA3AF' : '#6B7280'
                    }
                }
            },
            interaction: {
                intersect: false,
                mode: 'index'
            }
        }
    });
}

function updateTopCurators() {
    const container = document.getElementById('top-curators-list');
    if (!container || !dashboardData.topCurators) return;
    
    container.innerHTML = '';
    
    dashboardData.topCurators.slice(0, 5).forEach((curator, index) => {
        const curatorElement = document.createElement('div');
        curatorElement.className = 'flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700 rounded-xl';
        
        const ratingClass = getRatingClass(curator.rating_level);
        
        curatorElement.innerHTML = `
            <div class="flex items-center space-x-3">
                <div class="w-8 h-8 bg-blue-100 dark:bg-blue-900 rounded-full flex items-center justify-center text-sm font-bold text-blue-600 dark:text-blue-300">
                    ${index + 1}
                </div>
                <div>
                    <p class="font-medium text-gray-900 dark:text-white">${curator.name}</p>
                    <p class="text-sm ${ratingClass}">${curator.rating_level}</p>
                </div>
            </div>
            <div class="text-right">
                <p class="font-bold text-gray-900 dark:text-white">${curator.total_points}</p>
                <p class="text-sm text-gray-500 dark:text-gray-400">points</p>
            </div>
        `;
        
        container.appendChild(curatorElement);
    });
}

function updateRecentActivities() {
    const container = document.getElementById('recent-activities');
    if (!container || !dashboardData.recentActivities) return;
    
    container.innerHTML = '';
    
    if (dashboardData.recentActivities.length === 0) {
        container.innerHTML = `
            <div class="text-center py-8">
                <i class="fas fa-inbox text-4xl text-gray-300 dark:text-gray-600 mb-4"></i>
                <p class="text-gray-500 dark:text-gray-400">No recent activities</p>
            </div>
        `;
        return;
    }
    
    dashboardData.recentActivities.slice(0, 10).forEach(activity => {
        const activityElement = document.createElement('div');
        activityElement.className = 'flex items-center space-x-4 p-4 border border-gray-200 dark:border-gray-600 rounded-xl hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors';
        
        const icon = getActivityIcon(activity.type);
        const timeAgo = getTimeAgo(activity.timestamp);
        
        activityElement.innerHTML = `
            <div class="flex-shrink-0">
                <div class="w-10 h-10 bg-blue-100 dark:bg-blue-900 rounded-full flex items-center justify-center">
                    <i class="${icon} text-blue-600 dark:text-blue-300"></i>
                </div>
            </div>
            <div class="flex-1 min-w-0">
                <p class="text-sm font-medium text-gray-900 dark:text-white">
                    ${activity.curator_name || 'Unknown Curator'}
                </p>
                <p class="text-sm text-gray-500 dark:text-gray-400">
                    ${activity.type} in ${activity.server_name || 'Unknown Server'}
                </p>
            </div>
            <div class="flex-shrink-0">
                <p class="text-sm text-gray-500 dark:text-gray-400">${timeAgo}</p>
                <p class="text-xs text-blue-600 dark:text-blue-300 font-medium">+${activity.points} pts</p>
            </div>
        `;
        
        container.appendChild(activityElement);
    });
}

// Utility functions
function getRatingClass(rating) {
    const ratingMap = {
        'Великолепно': 'rating-excellent',
        'Хорошо': 'rating-good',
        'Нормально': 'rating-normal',
        'Плохо': 'rating-poor',
        'Ужасно': 'rating-terrible'
    };
    return `text-sm ${ratingMap[rating] || 'text-gray-500'}`;
}

function getActivityIcon(type) {
    const iconMap = {
        'message': 'fas fa-comment',
        'reaction': 'fas fa-heart',
        'reply': 'fas fa-reply',
        'task_verification': 'fas fa-check-circle'
    };
    return iconMap[type] || 'fas fa-circle';
}

function getTimeAgo(timestamp) {
    const now = new Date();
    const time = new Date(timestamp);
    const diffMs = now - time;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);
    
    if (diffMins < 1) return 'just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    return `${diffDays}d ago`;
}

// Loading states
function showLoading(show) {
    const overlay = document.getElementById('loading-overlay');
    if (overlay) {
        if (show) {
            overlay.classList.remove('hidden');
        } else {
            overlay.classList.add('hidden');
        }
    }
}

// Toast notifications
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    
    const icon = {
        'success': 'fas fa-check-circle',
        'error': 'fas fa-exclamation-circle',
        'warning': 'fas fa-exclamation-triangle',
        'info': 'fas fa-info-circle'
    }[type] || 'fas fa-info-circle';
    
    toast.innerHTML = `
        <div class="flex items-center space-x-3">
            <i class="${icon}"></i>
            <span>${message}</span>
            <button onclick="this.parentElement.parentElement.remove()" class="ml-4 text-gray-400 hover:text-gray-600">
                <i class="fas fa-times"></i>
            </button>
        </div>
    `;
    
    document.body.appendChild(toast);
    
    // Show toast
    setTimeout(() => toast.classList.add('show'), 100);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, 5000);
}

// Data refresh
async function refreshData() {
    const button = event.target.closest('button');
    const icon = button.querySelector('i');
    
    // Add spinning animation
    icon.classList.add('fa-spin');
    
    try {
        await loadSectionData(currentSection);
        showToast('Data refreshed successfully', 'success');
    } catch (error) {
        showToast('Failed to refresh data', 'error');
    } finally {
        icon.classList.remove('fa-spin');
    }
}

// Section-specific data loading
async function loadSectionData(sectionName) {
    switch (sectionName) {
        case 'dashboard':
            await loadDashboardData();
            break;
        case 'curators':
            await loadCuratorsData();
            break;
        case 'activities':
            await loadActivitiesData();
            break;
        case 'servers':
            await loadServersData();
            break;
        case 'reports':
            await loadReportsData();
            break;
        case 'settings':
            await loadSettingsData();
            break;
        case 'backup':
            await loadBackupData();
            break;
    }
}

// Load section data - updated to include curators
async function loadCuratorsData() {
    if (window.loadCuratorsData && typeof window.loadCuratorsData === 'function') {
        await window.loadCuratorsData();
    } else {
        console.log('Loading curators data...');
    }
}

async function loadActivitiesData() {
    if (window.loadActivitiesData && typeof window.loadActivitiesData === 'function') {
        await window.loadActivitiesData();
    } else {
        console.log('Loading activities data...');
    }
}

async function loadServersData() {
    if (window.loadServersData && typeof window.loadServersData === 'function') {
        await window.loadServersData();
    } else {
        console.log('Loading servers data...');
    }
}

async function loadReportsData() {
    if (window.loadReportsData && typeof window.loadReportsData === 'function') {
        await window.loadReportsData();
    } else {
        console.log('Loading reports data...');
    }
}

async function loadSettingsData() {
    if (window.loadSettingsData && typeof window.loadSettingsData === 'function') {
        await window.loadSettingsData();
    } else {
        console.log('Loading settings data...');
    }
}

async function loadBackupData() {
    if (window.loadBackupData && typeof window.loadBackupData === 'function') {
        await window.loadBackupData();
    } else {
        console.log('Loading backup data...');
    }
}

// Chart theme updates
function updateChartsTheme() {
    Object.values(charts).forEach(chart => {
        if (chart && chart.options) {
            // Update axis colors
            if (chart.options.scales) {
                Object.values(chart.options.scales).forEach(scale => {
                    if (scale.ticks) {
                        scale.ticks.color = isDarkMode ? '#9CA3AF' : '#6B7280';
                    }
                    if (scale.grid) {
                        scale.grid.color = isDarkMode ? '#374151' : '#E5E7EB';
                    }
                });
            }
            
            chart.update();
        }
    });
}

// Event listeners
function setupEventListeners() {
    // Handle responsive navigation
    window.addEventListener('resize', handleResize);
    
    // Handle keyboard shortcuts
    document.addEventListener('keydown', handleKeyboardShortcuts);
    
    // Handle offline/online status
    window.addEventListener('online', () => {
        showToast('Connection restored', 'success');
    });
    
    window.addEventListener('offline', () => {
        showToast('Connection lost', 'warning');
    });
}

function handleResize() {
    // Update charts on resize
    Object.values(charts).forEach(chart => {
        if (chart) {
            chart.resize();
        }
    });
}

function handleKeyboardShortcuts(event) {
    // Ctrl/Cmd + R to refresh
    if ((event.ctrlKey || event.metaKey) && event.key === 'r') {
        event.preventDefault();
        refreshData();
    }
    
    // Ctrl/Cmd + D to toggle dark mode
    if ((event.ctrlKey || event.metaKey) && event.key === 'd') {
        event.preventDefault();
        toggleTheme();
    }
}

// Modal functions (placeholder)
function openAddCuratorModal() {
    showToast('Add curator modal coming soon', 'info');
}

// Error handling
window.addEventListener('error', function(event) {
    console.error('JavaScript error:', event.error);
    showToast('An unexpected error occurred', 'error');
});

// Unhandled promise rejection handling
window.addEventListener('unhandledrejection', function(event) {
    console.error('Unhandled promise rejection:', event.reason);
    showToast('A network error occurred', 'error');
    event.preventDefault();
});

// Export functions for global access
window.showSection = showSection;
window.toggleTheme = toggleTheme;
window.refreshData = refreshData;
window.openAddCuratorModal = openAddCuratorModal;
