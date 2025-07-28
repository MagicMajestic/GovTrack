// GovTracker2 Python Migration by Replit Agent - Activities Management

let activitiesData = [];
let activitiesAutoRefreshInterval = null;

// Load activities data
async function loadActivitiesData() {
    console.log('Loading activities data...');
    try {
        const response = await fetch('/api/activities');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        activitiesData = await response.json();
        updateActivitiesGrid();
        
    } catch (error) {
        console.error('Error loading activities data:', error);
        showToast('Failed to load activities data', 'error');
    }
}

// Start auto-refresh for activities
function startActivitiesAutoRefresh() {
    if (activitiesAutoRefreshInterval) {
        clearInterval(activitiesAutoRefreshInterval);
    }
    
    activitiesAutoRefreshInterval = setInterval(() => {
        loadActivitiesData();
    }, 30000); // Refresh every 30 seconds
}

// Stop auto-refresh for activities
function stopActivitiesAutoRefresh() {
    if (activitiesAutoRefreshInterval) {
        clearInterval(activitiesAutoRefreshInterval);
        activitiesAutoRefreshInterval = null;
    }
}

// Update activities grid
function updateActivitiesGrid() {
    const grid = document.getElementById('activities-grid');
    if (!grid) return;
    
    grid.innerHTML = '';
    
    if (activitiesData.length === 0) {
        grid.innerHTML = `
            <div class="text-center py-12">
                <i class="fas fa-chart-line text-6xl text-gray-300 dark:text-gray-600 mb-4"></i>
                <h3 class="text-xl font-medium text-gray-900 dark:text-white mb-2">No Activities Found</h3>
                <p class="text-gray-500 dark:text-gray-400 mb-6">Activities will appear here as curators interact with Discord servers</p>
            </div>
        `;
        return;
    }
    
    // Group activities by date
    const groupedActivities = groupActivitiesByDate(activitiesData);
    
    Object.entries(groupedActivities).forEach(([date, activities]) => {
        const dateSection = createDateSection(date, activities);
        grid.appendChild(dateSection);
    });
}

// Group activities by date
function groupActivitiesByDate(activities) {
    return activities.reduce((groups, activity) => {
        const date = new Date(activity.timestamp).toDateString();
        if (!groups[date]) {
            groups[date] = [];
        }
        groups[date].push(activity);
        return groups;
    }, {});
}

// Create date section
function createDateSection(date, activities) {
    const section = document.createElement('div');
    section.className = 'bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6 border border-gray-200 dark:border-gray-700';
    
    const totalPoints = activities.reduce((sum, activity) => sum + activity.points, 0);
    
    section.innerHTML = `
        <div class="flex items-center justify-between mb-4">
            <h3 class="text-lg font-semibold text-gray-900 dark:text-white">${date}</h3>
            <div class="flex items-center space-x-4">
                <span class="text-sm text-gray-500 dark:text-gray-400">${activities.length} activities</span>
                <span class="px-3 py-1 bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-300 rounded-full text-sm font-medium">
                    +${totalPoints} points
                </span>
            </div>
        </div>
        <div class="space-y-3">
            ${activities.map(activity => createActivityItem(activity)).join('')}
        </div>
    `;
    
    return section;
}

// Create activity item
function createActivityItem(activity) {
    const icon = getActivityIcon(activity.type);
    const timeFormatted = new Date(activity.timestamp).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
    
    return `
        <div class="flex items-center space-x-4 p-3 bg-gray-50 dark:bg-gray-700 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-600 transition-colors">
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
                ${activity.content ? `<p class="text-xs text-gray-400 dark:text-gray-500 truncate">${activity.content}</p>` : ''}
            </div>
            <div class="flex-shrink-0 text-right">
                <p class="text-sm text-gray-500 dark:text-gray-400">${timeFormatted}</p>
                <p class="text-xs text-blue-600 dark:text-blue-300 font-medium">+${activity.points} pts</p>
            </div>
        </div>
    `;
}

// Show add activity modal
function showAddActivityModal() {
    showToast('Activity logging coming soon', 'info');
}

// Initialize activities section
function initializeActivitiesSection() {
    loadActivitiesData();
    startActivitiesAutoRefresh();
}

// Clean up activities section
function cleanupActivitiesSection() {
    stopActivitiesAutoRefresh();
}

// Make functions available globally
window.loadActivitiesData = loadActivitiesData;
window.initializeActivitiesSection = initializeActivitiesSection;
window.cleanupActivitiesSection = cleanupActivitiesSection;
window.showAddActivityModal = showAddActivityModal;