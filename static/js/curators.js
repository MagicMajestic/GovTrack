// GovTracker2 Python Migration by Replit Agent - Curators Management

let curatorsData = [];

// Global variables
let currentEditingCuratorId = null;
let availableServers = [];

// Auto-refresh interval (30 seconds)
let autoRefreshInterval = null;

// Load curators data
async function loadCuratorsData() {
    console.log('Loading curators data...');
    try {
        const response = await fetch('/api/curators');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        curatorsData = await response.json();
        await loadAvailableServers();
        updateCuratorsGrid();
        
    } catch (error) {
        console.error('Error loading curators data:', error);
        showToast('Не удалось загрузить данные кураторов', 'error');
    }
}

// Start auto-refresh
function startAutoRefresh() {
    if (autoRefreshInterval) {
        clearInterval(autoRefreshInterval);
    }
    
    autoRefreshInterval = setInterval(() => {
        loadCuratorsData();
    }, 30000); // Refresh every 30 seconds
}

// Stop auto-refresh
function stopAutoRefresh() {
    if (autoRefreshInterval) {
        clearInterval(autoRefreshInterval);
        autoRefreshInterval = null;
    }
}

// Load available servers for curator assignment
async function loadAvailableServers() {
    try {
        const response = await fetch('/api/servers');
        if (response.ok) {
            availableServers = await response.json();
        }
    } catch (error) {
        console.error('Error loading servers:', error);
        availableServers = [];
    }
}

// Update curators grid
function updateCuratorsGrid() {
    const grid = document.getElementById('curators-grid');
    if (!grid) return;
    
    grid.innerHTML = '';
    
    if (curatorsData.length === 0) {
        grid.innerHTML = `
            <div class="col-span-full text-center py-12">
                <i class="fas fa-users text-6xl text-gray-300 dark:text-gray-600 mb-4"></i>
                <h3 class="text-xl font-medium text-gray-900 dark:text-white mb-2">Кураторы не найдены</h3>
                <p class="text-gray-500 dark:text-gray-400 mb-6">Начните с добавления первого куратора в систему</p>
                <button onclick="showAddCuratorModal()" class="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg">
                    <i class="fas fa-plus mr-2"></i>Добавить первого куратора
                </button>
            </div>
        `;
        return;
    }
    
    curatorsData.forEach(curator => {
        const curatorCard = createCuratorCard(curator);
        grid.appendChild(curatorCard);
    });
}

// Create curator card
function createCuratorCard(curator) {
    const card = document.createElement('div');
    card.className = 'bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6 hover:shadow-xl transition-shadow border border-gray-200 dark:border-gray-700';
    
    const ratingClass = getRatingClass(curator.rating_level);
    const ratingColor = getRatingColor(curator.rating_level);
    
    card.innerHTML = `
        <div class="flex items-start justify-between mb-4">
            <div class="flex items-center space-x-3">
                <div class="w-12 h-12 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center text-white font-bold text-lg">
                    ${curator.name.charAt(0).toUpperCase()}
                </div>
                <div>
                    <h3 class="font-bold text-gray-900 dark:text-white">${curator.name}</h3>
                    <p class="text-sm text-gray-500 dark:text-gray-400">${curator.curator_type || 'Curator'}</p>
                </div>
            </div>
            <div class="flex space-x-2">
                <button onclick="editCurator(${curator.id})" class="text-blue-600 hover:text-blue-800 dark:text-blue-400">
                    <i class="fas fa-edit"></i>
                </button>
                <button onclick="deleteCurator(${curator.id})" class="text-red-600 hover:text-red-800 dark:text-red-400">
                    <i class="fas fa-trash"></i>
                </button>
            </div>
        </div>
        
        <div class="space-y-3">
            <div class="flex justify-between items-center">
                <span class="text-sm text-gray-600 dark:text-gray-400">Rating</span>
                <span class="px-2 py-1 rounded-full text-xs font-medium ${ratingColor}">
                    ${curator.rating_level}
                </span>
            </div>
            
            <div class="flex justify-between items-center">
                <span class="text-sm text-gray-600 dark:text-gray-400">Total Points</span>
                <span class="font-bold text-gray-900 dark:text-white">${curator.total_points}</span>
            </div>
            
            ${curator.subdivision ? `
                <div class="flex justify-between items-center">
                    <span class="text-sm text-gray-600 dark:text-gray-400">Subdivision</span>
                    <span class="text-sm text-gray-900 dark:text-white">${curator.subdivision}</span>
                </div>
            ` : ''}
            
            ${curator.factions && curator.factions.length > 0 ? `
                <div>
                    <span class="text-sm text-gray-600 dark:text-gray-400 block mb-2">Factions</span>
                    <div class="flex flex-wrap gap-1">
                        ${curator.factions.map(faction => 
                            `<span class="px-2 py-1 bg-gray-100 dark:bg-gray-700 rounded text-xs text-gray-700 dark:text-gray-300">${faction}</span>`
                        ).join('')}
                    </div>
                </div>
            ` : ''}
        </div>
        
        <div class="mt-4 pt-4 border-t border-gray-200 dark:border-gray-600">
            <button onclick="viewCuratorDetails(${curator.id})" class="w-full bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 py-2 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors">
                <i class="fas fa-chart-line mr-2"></i>View Details
            </button>
        </div>
    `;
    
    return card;
}

// Get rating color class
function getRatingColor(rating) {
    const colorMap = {
        'Великолепно': 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300',
        'Хорошо': 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300',
        'Нормально': 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300',
        'Плохо': 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-300',
        'Ужасно': 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300'
    };
    return colorMap[rating] || 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-300';
}

// Show add curator modal
function showAddCuratorModal() {
    currentEditingCuratorId = null;
    document.getElementById('curator-modal-title').textContent = 'Добавить куратора';
    document.getElementById('curator-form').reset();
    populateServerCheckboxes();
    document.getElementById('curator-modal').classList.remove('hidden');
}

// Hide add curator modal
function hideAddCuratorModal() {
    const modal = document.getElementById('addCuratorModal');
    if (modal) {
        modal.classList.add('hidden');
        document.getElementById('addCuratorForm').reset();
    }
}

// Submit add curator form
async function submitAddCurator(event) {
    event.preventDefault();
    
    const formData = {
        discord_id: document.getElementById('curatorDiscordId').value.trim(),
        name: document.getElementById('curatorName').value.trim(),
        curator_type: document.getElementById('curatorType').value,
        subdivision: document.getElementById('curatorSubdivision').value.trim(),
        factions: document.getElementById('curatorFactions').value
            .split(',')
            .map(f => f.trim())
            .filter(f => f.length > 0)
    };
    
    try {
        const response = await fetch('/api/curators', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to add curator');
        }
        
        const newCurator = await response.json();
        curatorsData.push(newCurator);
        updateCuratorsGrid();
        hideAddCuratorModal();
        showToast('Curator added successfully', 'success');
        
    } catch (error) {
        console.error('Error adding curator:', error);
        showToast(error.message, 'error');
    }
}

// Edit curator
function editCurator(curatorId) {
    const curator = curatorsData.find(c => c.id === curatorId);
    if (!curator) return;
    
    currentEditingCuratorId = curatorId;
    document.getElementById('curator-modal-title').textContent = 'Редактировать куратора';
    
    // Populate form fields
    document.getElementById('curator-discord-id').value = curator.discord_id;
    document.getElementById('curator-name').value = curator.name;
    
    populateServerCheckboxes(curator.assigned_servers || []);
    document.getElementById('curator-modal').classList.remove('hidden');
}

// Close curator modal
function closeCuratorModal() {
    document.getElementById('curator-modal').classList.add('hidden');
    currentEditingCuratorId = null;
}

// Populate server checkboxes
function populateServerCheckboxes(selectedServerIds = []) {
    const container = document.getElementById('server-checkboxes');
    container.innerHTML = '';
    
    if (availableServers.length === 0) {
        container.innerHTML = '<p class="text-sm text-gray-500 dark:text-gray-400">Нет доступных серверов</p>';
        return;
    }
    
    availableServers.forEach(server => {
        const isChecked = selectedServerIds.includes(server.id);
        const checkbox = document.createElement('label');
        checkbox.className = 'flex items-center space-x-2 cursor-pointer';
        checkbox.innerHTML = `
            <input type="checkbox" value="${server.id}" ${isChecked ? 'checked' : ''} class="server-checkbox">
            <span class="text-sm text-gray-700 dark:text-gray-300">${server.name}</span>
        `;
        container.appendChild(checkbox);
    });
}

// Handle curator form submission
document.addEventListener('DOMContentLoaded', function() {
    const curatorForm = document.getElementById('curator-form');
    if (curatorForm) {
        curatorForm.addEventListener('submit', async function(e) {
    e.preventDefault();
    
    // Get selected server IDs
    const selectedServers = Array.from(document.querySelectorAll('.server-checkbox:checked'))
        .map(checkbox => parseInt(checkbox.value));
    
    const formData = {
        discord_id: document.getElementById('curator-discord-id').value,
        name: document.getElementById('curator-name').value,
        assigned_servers: selectedServers
    };
    
    try {
        const url = currentEditingCuratorId ? `/api/curators/${currentEditingCuratorId}` : '/api/curators';
        const method = currentEditingCuratorId ? 'PUT' : 'POST';
        
        const response = await fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to save curator');
        }
        
        const result = await response.json();
        showToast(currentEditingCuratorId ? 'Куратор обновлен' : 'Куратор добавлен', 'success');
        closeCuratorModal();
        loadCuratorsData(); // Reload the list
        
    } catch (error) {
        console.error('Error saving curator:', error);
        showToast(error.message, 'error');
    }
        });
    }
});

// Delete curator
async function deleteCurator(curatorId) {
    if (!confirm('Вы уверены, что хотите удалить этого куратора? Это действие нельзя отменить.')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/curators/${curatorId}`, {
            method: 'DELETE'
        });
        
        if (!response.ok) {
            throw new Error('Failed to delete curator');
        }
        
        curatorsData = curatorsData.filter(c => c.id !== curatorId);
        updateCuratorsGrid();
        showToast('Curator deleted successfully', 'success');
        
    } catch (error) {
        console.error('Error deleting curator:', error);
        showToast('Не удалось удалить куратора', 'error');
    }
}

// View curator details (fast version using existing data + quick API call)
async function viewCuratorDetails(curatorId) {
    try {
        // Get the curator from current data first for instant modal display
        const curator = curatorsData.find(c => c.id === curatorId);
        if (!curator) {
            throw new Error('Curator not found');
        }
        
        // Show modal immediately with existing data
        showCuratorDetailsModal({ curator, loading: true });
        
        // Then fetch fresh details in background
        const response = await fetch(`/api/curators/${curatorId}`);
        if (!response.ok) {
            throw new Error('Failed to load curator details');
        }
        
        const details = await response.json();
        
        // Update modal with fresh data
        showCuratorDetailsModal({ curator: details, loading: false });
        
    } catch (error) {
        console.error('Error loading curator details:', error);
        showToast('Не удалось загрузить детали куратора', 'error');
    }
}

// Show curator details modal
function showCuratorDetailsModal(details) {
    const curator = details.curator;
    const isLoading = details.loading;
    
    // Use weekly_stats if available, otherwise use main stats
    const stats = curator.weekly_stats || curator;
    
    // Remove existing modal if present
    const existingModal = document.querySelector('.curator-details-modal');
    if (existingModal) {
        existingModal.remove();
    }
    
    const modal = document.createElement('div');
    modal.className = 'curator-details-modal fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4';
    modal.onclick = (e) => {
        if (e.target === modal) modal.remove();
    };
    
    modal.innerHTML = `
        <div class="bg-white dark:bg-gray-800 rounded-xl shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
            <div class="sticky top-0 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 p-6 rounded-t-xl">
                <div class="flex justify-between items-center">
                    <div class="flex items-center space-x-4">
                        <div class="w-16 h-16 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center text-white font-bold text-2xl">
                            ${curator.name.charAt(0).toUpperCase()}
                        </div>
                        <div>
                            <h2 class="text-2xl font-bold text-gray-900 dark:text-white">${curator.name}</h2>
                            <p class="text-gray-500 dark:text-gray-400">${curator.curator_type || 'Куратор'}</p>
                            <div class="flex items-center space-x-4 mt-2">
                                <span class="px-3 py-1 rounded-full text-sm font-medium ${getRatingColor(curator.rating_level)}">
                                    ${curator.rating_level}
                                </span>
                                <span class="text-lg font-bold text-gray-900 dark:text-white">${curator.total_points || 0} очков</span>
                                ${isLoading ? '<div class="animate-pulse text-sm text-gray-500">Загрузка...</div>' : ''}
                            </div>
                        </div>
                    </div>
                    <button onclick="this.closest('.fixed').remove()" class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300">
                        <i class="fas fa-times text-2xl"></i>
                    </button>
                </div>
            </div>
            
            <div class="p-6">
                <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
                    <div class="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4">
                        <h3 class="text-sm font-medium text-blue-600 dark:text-blue-400 mb-2">Всего активностей</h3>
                        <p class="text-3xl font-bold text-blue-700 dark:text-blue-300">${stats.total_activities || curator.total_activities || 0}</p>
                        <p class="text-xs text-blue-500 dark:text-blue-400 mt-1">За последнюю неделю</p>
                    </div>
                    <div class="bg-green-50 dark:bg-green-900/20 rounded-lg p-4">
                        <h3 class="text-sm font-medium text-green-600 dark:text-green-400 mb-2">Сообщения</h3>
                        <p class="text-3xl font-bold text-green-700 dark:text-green-300">${stats.messages || curator.messages || 0}</p>
                        <p class="text-xs text-green-500 dark:text-green-400 mt-1">+${(stats.messages || curator.messages || 0) * 3} очков</p>
                    </div>
                    <div class="bg-purple-50 dark:bg-purple-900/20 rounded-lg p-4">
                        <h3 class="text-sm font-medium text-purple-600 dark:text-purple-400 mb-2">Реакции</h3>
                        <p class="text-3xl font-bold text-purple-700 dark:text-purple-300">${stats.reactions || curator.reactions || 0}</p>
                        <p class="text-xs text-purple-500 dark:text-purple-400 mt-1">+${(stats.reactions || curator.reactions || 0) * 1} очков</p>
                    </div>
                    <div class="bg-yellow-50 dark:bg-yellow-900/20 rounded-lg p-4">
                        <h3 class="text-sm font-medium text-yellow-600 dark:text-yellow-400 mb-2">Ответы</h3>
                        <p class="text-3xl font-bold text-yellow-700 dark:text-yellow-300">${stats.replies || curator.replies || 0}</p>
                        <p class="text-xs text-yellow-500 dark:text-yellow-400 mt-1">+${(stats.replies || curator.replies || 0) * 2} очков</p>
                    </div>
                    <div class="bg-red-50 dark:bg-red-900/20 rounded-lg p-4">
                        <h3 class="text-sm font-medium text-red-600 dark:text-red-400 mb-2">Проверки задач</h3>
                        <p class="text-3xl font-bold text-red-700 dark:text-red-300">${curator.task_verifications || 0}</p>
                        <p class="text-xs text-red-500 dark:text-red-400 mt-1">+${(curator.task_verifications || 0) * 5} очков</p>
                    </div>
                    <div class="bg-gray-50 dark:bg-gray-900/20 rounded-lg p-4">
                        <h3 class="text-sm font-medium text-gray-600 dark:text-gray-400 mb-2">Среднее время ответа</h3>
                        <p class="text-3xl font-bold text-gray-700 dark:text-gray-300">${curator.average_response_time || 0}с</p>
                        <p class="text-xs text-gray-500 dark:text-gray-400 mt-1">На запросы помощи</p>
                    </div>
                </div>
                
                <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <div class="bg-gray-50 dark:bg-gray-900/20 rounded-lg p-4">
                        <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">Информация о кураторе</h3>
                        <div class="space-y-3">
                            <div class="flex justify-between">
                                <span class="text-gray-600 dark:text-gray-400">Discord ID:</span>
                                <span class="text-gray-900 dark:text-white font-mono">${curator.discord_id}</span>
                            </div>
                            <div class="flex justify-between">
                                <span class="text-gray-600 dark:text-gray-400">Создан:</span>
                                <span class="text-gray-900 dark:text-white">${new Date(curator.created_at).toLocaleDateString('ru-RU')}</span>
                            </div>
                            <div class="flex justify-between">
                                <span class="text-gray-600 dark:text-gray-400">Последнее обновление:</span>
                                <span class="text-gray-900 dark:text-white">${new Date(curator.updated_at).toLocaleDateString('ru-RU')}</span>
                            </div>
                        </div>
                    </div>
                    
                    <div class="bg-gray-50 dark:bg-gray-900/20 rounded-lg p-4">
                        <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">Прогресс рейтинга</h3>
                        <div class="space-y-3">
                            <div class="flex justify-between items-center">
                                <span class="text-gray-600 dark:text-gray-400">Текущий рейтинг:</span>
                                <span class="px-3 py-1 rounded-full text-sm font-medium ${getRatingColor(curator.rating_level)}">
                                    ${curator.rating_level}
                                </span>
                            </div>
                            <div class="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                                <div class="bg-blue-600 h-2 rounded-full transition-all duration-300" style="width: ${Math.min((curator.total_points || 0) / 50 * 100, 100)}%"></div>
                            </div>
                            <div class="flex justify-between text-xs text-gray-500 dark:text-gray-400">
                                <span>0</span>
                                <span>20 (Нормально)</span>
                                <span>35 (Хорошо)</span>
                                <span>50+ (Великолепно)</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>`;
        
    document.body.appendChild(modal);
                        <h3 class="text-sm font-medium text-gray-600 dark:text-gray-400 mb-2">Avg Response Time</h3>
                        <p class="text-3xl font-bold text-gray-700 dark:text-gray-300">${responseStats.average_response_time || 0}s</p>
                    </div>
                </div>
                
                ${details.assigned_servers_details && details.assigned_servers_details.length > 0 ? `
                    <div class="mb-8">
                        <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">Assigned Servers</h3>
                        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                            ${details.assigned_servers_details.map(server => `
                                <div class="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
                                    <h4 class="font-medium text-gray-900 dark:text-white">${server.name}</h4>
                                    <p class="text-sm text-gray-500 dark:text-gray-400">Server ID: ${server.server_id}</p>
                                    <p class="text-sm text-gray-500 dark:text-gray-400">Status: ${server.is_active ? 'Active' : 'Inactive'}</p>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                ` : ''}
                
                ${recentActivities.length > 0 ? `
                    <div>
                        <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">Recent Activities</h3>
                        <div class="bg-gray-50 dark:bg-gray-700 rounded-lg overflow-hidden">
                            <div class="max-h-64 overflow-y-auto">
                                ${recentActivities.slice(0, 10).map(activity => `
                                    <div class="flex justify-between items-center p-3 border-b border-gray-200 dark:border-gray-600 last:border-b-0">
                                        <div>
                                            <span class="text-sm font-medium text-gray-900 dark:text-white capitalize">${activity.type}</span>
                                            ${activity.server_name ? `<span class="text-xs text-gray-500 dark:text-gray-400 ml-2">in ${activity.server_name}</span>` : ''}
                                            ${activity.content ? `<p class="text-xs text-gray-600 dark:text-gray-300 mt-1">${activity.content.substring(0, 100)}${activity.content.length > 100 ? '...' : ''}</p>` : ''}
                                        </div>
                                        <div class="text-right">
                                            <div class="text-sm font-medium text-blue-600 dark:text-blue-400">+${activity.points} pts</div>
                                            <div class="text-xs text-gray-500 dark:text-gray-400">${new Date(activity.timestamp).toLocaleDateString()}</div>
                                        </div>
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                    </div>
                ` : `
                    <div class="text-center py-8">
                        <i class="fas fa-chart-line text-4xl text-gray-300 dark:text-gray-600 mb-4"></i>
                        <p class="text-gray-500 dark:text-gray-400">No recent activities</p>
                    </div>
                `}
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
}

// viewCuratorDetails function is implemented above at line 330

// Initialize auto-refresh when curators section is loaded
function initializeCuratorsSection() {
    loadCuratorsData();
    startAutoRefresh();
}

// Clean up when leaving curators section
function cleanupCuratorsSection() {
    stopAutoRefresh();
}

// Make functions available globally
window.loadCuratorsData = loadCuratorsData;
window.showAddCuratorModal = showAddCuratorModal;
window.hideAddCuratorModal = hideAddCuratorModal;
window.submitAddCurator = submitAddCurator;
window.editCurator = editCurator;
window.deleteCurator = deleteCurator;
window.viewCuratorDetails = viewCuratorDetails;
window.initializeCuratorsSection = initializeCuratorsSection;
window.cleanupCuratorsSection = cleanupCuratorsSection;