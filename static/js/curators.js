// GovTracker2 Python Migration by Replit Agent - Curators Management

let curatorsData = [];

// Global variables
let currentEditingCuratorId = null;
let availableServers = [];

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

// View curator details
function viewCuratorDetails(curatorId) {
    // TODO: Implement detailed view
    showToast('Detailed view coming soon', 'info');
}

// Make functions available globally
window.loadCuratorsData = loadCuratorsData;
window.showAddCuratorModal = showAddCuratorModal;
window.hideAddCuratorModal = hideAddCuratorModal;
window.submitAddCurator = submitAddCurator;
window.editCurator = editCurator;
window.deleteCurator = deleteCurator;
window.viewCuratorDetails = viewCuratorDetails;