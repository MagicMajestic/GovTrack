// GovTracker2 Python Migration by Replit Agent - Servers Management

let serversData = [];

// Load servers data
async function loadServersData() {
    console.log('Loading servers data...');
    try {
        const response = await fetch('/api/servers');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        serversData = await response.json();
        updateServersGrid();
        
    } catch (error) {
        console.error('Error loading servers data:', error);
        showToast('Failed to load servers data', 'error');
    }
}

// Update servers grid
function updateServersGrid() {
    const grid = document.getElementById('servers-grid');
    if (!grid) return;
    
    grid.innerHTML = '';
    
    if (serversData.length === 0) {
        grid.innerHTML = `
            <div class="col-span-full text-center py-12">
                <i class="fas fa-server text-6xl text-gray-300 dark:text-gray-600 mb-4"></i>
                <h3 class="text-xl font-medium text-gray-900 dark:text-white mb-2">No Servers Configured</h3>
                <p class="text-gray-500 dark:text-gray-400 mb-6">Add Discord servers to start monitoring curator activities</p>
                <button onclick="showAddServerModal()" class="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg">
                    <i class="fas fa-plus mr-2"></i>Add First Server
                </button>
            </div>
        `;
        return;
    }
    
    serversData.forEach(server => {
        const serverCard = createServerCard(server);
        grid.appendChild(serverCard);
    });
}

// Create server card
function createServerCard(server) {
    const card = document.createElement('div');
    card.className = 'bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6 hover:shadow-xl transition-shadow border border-gray-200 dark:border-gray-700';
    
    const statusColor = server.is_active ? 'text-green-600 bg-green-100 dark:bg-green-900 dark:text-green-300' : 'text-red-600 bg-red-100 dark:bg-red-900 dark:text-red-300';
    const statusText = server.is_active ? 'Active' : 'Inactive';
    
    card.innerHTML = `
        <div class="flex items-start justify-between mb-4">
            <div class="flex items-center space-x-3">
                <div class="w-12 h-12 bg-gradient-to-br from-purple-500 to-pink-600 rounded-full flex items-center justify-center text-white font-bold text-lg">
                    <i class="fab fa-discord"></i>
                </div>
                <div>
                    <h3 class="font-bold text-gray-900 dark:text-white">${server.name}</h3>
                    <p class="text-sm text-gray-500 dark:text-gray-400">ID: ${server.server_id}</p>
                </div>
            </div>
            <div class="flex space-x-2">
                <button onclick="editServer(${server.id})" class="text-blue-600 hover:text-blue-800 dark:text-blue-400">
                    <i class="fas fa-edit"></i>
                </button>
                <button onclick="deleteServer(${server.id})" class="text-red-600 hover:text-red-800 dark:text-red-400">
                    <i class="fas fa-trash"></i>
                </button>
            </div>
        </div>
        
        <div class="space-y-3">
            <div class="flex justify-between items-center">
                <span class="text-sm text-gray-600 dark:text-gray-400">Status</span>
                <span class="px-2 py-1 rounded-full text-xs font-medium ${statusColor}">
                    ${statusText}
                </span>
            </div>
            
            ${server.role_tag_id ? `
                <div class="flex justify-between items-center">
                    <span class="text-sm text-gray-600 dark:text-gray-400">Role Tag ID</span>
                    <span class="text-sm text-gray-900 dark:text-white font-mono">${server.role_tag_id}</span>
                </div>
            ` : ''}
            
            <div class="flex justify-between items-center">
                <span class="text-sm text-gray-600 dark:text-gray-400">Added</span>
                <span class="text-sm text-gray-900 dark:text-white">${new Date(server.created_at).toLocaleDateString()}</span>
            </div>
        </div>
        
        <div class="mt-4 pt-4 border-t border-gray-200 dark:border-gray-600">
            <button onclick="viewServerStats(${server.id})" class="w-full bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 py-2 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors">
                <i class="fas fa-chart-bar mr-2"></i>View Statistics
            </button>
        </div>
    `;
    
    return card;
}

// Show add server modal
function showAddServerModal() {
    showToast('Server management coming soon', 'info');
}

// Edit server
function editServer(serverId) {
    showToast('Edit functionality coming soon', 'info');
}

// Delete server
async function deleteServer(serverId) {
    if (!confirm('Are you sure you want to delete this server? This will also remove all associated activity data.')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/servers/${serverId}`, {
            method: 'DELETE'
        });
        
        if (!response.ok) {
            throw new Error('Failed to delete server');
        }
        
        serversData = serversData.filter(s => s.id !== serverId);
        updateServersGrid();
        showToast('Server deleted successfully', 'success');
        
    } catch (error) {
        console.error('Error deleting server:', error);
        showToast('Failed to delete server', 'error');
    }
}

// View server statistics
function viewServerStats(serverId) {
    showToast('Server statistics coming soon', 'info');
}

// Make functions available globally
window.loadServersData = loadServersData;
window.showAddServerModal = showAddServerModal;
window.editServer = editServer;
window.deleteServer = deleteServer;
window.viewServerStats = viewServerStats;