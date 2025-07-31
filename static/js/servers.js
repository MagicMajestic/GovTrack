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
        showToast('Не удалось загрузить данные серверов', 'error');
    }
}

// Initialize default faction servers
async function initializeDefaultServers() {
    try {
        const response = await fetch('/api/servers/initialize', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        if (!response.ok) {
            throw new Error('Failed to initialize servers');
        }
        
        const result = await response.json();
        showToast(result.message, 'success');
        loadServersData(); // Reload servers list
    } catch (error) {
        console.error('Error initializing servers:', error);
        showToast('Ошибка инициализации серверов', 'error');
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
                <h3 class="text-xl font-medium text-gray-900 dark:text-white mb-2">Серверы не настроены</h3>
                <p class="text-gray-500 dark:text-gray-400 mb-6">Добавьте серверы Discord для начала отслеживания активности кураторов</p>
                <div class="flex justify-center space-x-4">
                    <button onclick="initializeDefaultServers()" class="bg-green-600 hover:bg-green-700 text-white px-6 py-3 rounded-lg">
                        <i class="fas fa-magic mr-2"></i>Инициализировать фракции
                    </button>
                    <button onclick="showAddServerModal()" class="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg">
                        <i class="fas fa-plus mr-2"></i>Добавить сервер
                    </button>
                </div>
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
    const statusText = server.is_active ? 'Активен' : 'Неактивен';
    
    card.innerHTML = `
        <div class="flex items-start justify-between mb-4">
            <div class="flex items-center space-x-3">
                <div class="w-10 h-10 bg-gradient-to-br from-purple-500 to-pink-600 rounded-full flex items-center justify-center text-white font-bold">
                    <i class="fab fa-discord"></i>
                </div>
                <div>
                    <h3 class="font-bold text-gray-900 dark:text-white text-sm">${server.name}</h3>
                    <span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${statusColor}">
                        ${statusText}
                    </span>
                </div>
            </div>
            <div class="flex space-x-2">
                <button onclick="editServer(${server.id})" class="text-blue-600 hover:text-blue-800 dark:text-blue-400 text-sm">
                    <i class="fas fa-edit"></i>
                </button>
                <button onclick="deleteServer(${server.id})" class="text-red-600 hover:text-red-800 dark:text-red-400 text-sm">
                    <i class="fas fa-trash"></i>
                </button>
            </div>
        </div>
        
        <div class="grid grid-cols-2 gap-3 text-center">
            <div class="bg-gray-50 dark:bg-gray-700 rounded-lg p-2">
                <div class="text-lg font-bold text-gray-900 dark:text-white">${server.curator_count || 0}</div>
                <div class="text-xs text-gray-500 dark:text-gray-400">Кураторы</div>
            </div>
            <div class="bg-gray-50 dark:bg-gray-700 rounded-lg p-2">
                <div class="text-lg font-bold text-gray-900 dark:text-white">${server.activity_count || 0}</div>
                <div class="text-xs text-gray-500 dark:text-gray-400">Активности</div>
            </div>
            <div class="bg-gray-50 dark:bg-gray-700 rounded-lg p-2">
                <div class="text-lg font-bold text-gray-900 dark:text-white">${server.avg_response_time || 0}s</div>
                <div class="text-xs text-gray-500 dark:text-gray-400">Время ответа</div>
            </div>
            <div class="bg-gray-50 dark:bg-gray-700 rounded-lg p-2">
                <div class="text-lg font-bold text-gray-900 dark:text-white">${server.reactions_count || 0}</div>
                <div class="text-xs text-gray-500 dark:text-gray-400">Реакции</div>
            </div>
        </div>
    `;
    
    return card;
}

// Global variables for modal state
let currentEditingServerId = null;

// Show add server modal
function showAddServerModal() {
    currentEditingServerId = null;
    document.getElementById('server-modal-title').textContent = 'Добавить сервер';
    document.getElementById('server-form').reset();
    document.getElementById('server-modal').classList.remove('hidden');
}

// Show edit server modal
function editServer(serverId) {
    const server = serversData.find(s => s.id === serverId);
    if (!server) return;
    
    currentEditingServerId = serverId;
    document.getElementById('server-modal-title').textContent = 'Редактировать сервер';
    
    // Populate form fields
    document.getElementById('server-id').value = server.server_id;
    document.getElementById('server-name').value = server.name;
    document.getElementById('curator-role-id').value = server.curator_role_id || '';
    document.getElementById('notification-channel-id').value = server.notification_channel_id || '';
    document.getElementById('tasks-channel-id').value = server.tasks_channel_id || '';
    document.getElementById('reminder-interval-seconds').value = server.reminder_interval_seconds || 300;
    document.getElementById('auto-reminder-enabled').checked = server.auto_reminder_enabled !== false;
    document.getElementById('server-active').checked = server.is_active;
    
    document.getElementById('server-modal').classList.remove('hidden');
}

// Close server modal
function closeServerModal() {
    document.getElementById('server-modal').classList.add('hidden');
    currentEditingServerId = null;
}

// Handle server form submission
document.addEventListener('DOMContentLoaded', function() {
    const serverForm = document.getElementById('server-form');
    if (serverForm) {
        serverForm.addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const formData = {
        server_id: document.getElementById('server-id').value,
        name: document.getElementById('server-name').value,
        curator_role_id: document.getElementById('curator-role-id').value,
        notification_channel_id: document.getElementById('notification-channel-id').value,
        tasks_channel_id: document.getElementById('tasks-channel-id').value,
        reminder_interval_seconds: parseInt(document.getElementById('reminder-interval-seconds').value) || 300,
        auto_reminder_enabled: document.getElementById('auto-reminder-enabled').checked,
        is_active: document.getElementById('server-active').checked
    };
    
    try {
        const url = currentEditingServerId ? `/api/servers/${currentEditingServerId}` : '/api/servers';
        const method = currentEditingServerId ? 'PUT' : 'POST';
        
        const response = await fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to save server');
        }
        
        const result = await response.json();
        showToast(currentEditingServerId ? 'Сервер обновлен' : 'Сервер добавлен', 'success');
        closeServerModal();
        loadServersData(); // Reload the list
        
    } catch (error) {
        console.error('Error saving server:', error);
        showToast(error.message, 'error');
    }
        });
    }
});

// Delete server
async function deleteServer(serverId) {
    if (!confirm('Вы уверены, что хотите удалить этот сервер? Это также удалит все связанные данные активности.')) {
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