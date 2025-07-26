// GovTracker2 Python Migration by Replit Agent - Backup Management

let backupsData = [];

// Load backup data
async function loadBackupData() {
    console.log('Loading backup data...');
    try {
        const response = await fetch('/api/backup');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        backupsData = await response.json();
        updateBackupList();
        updateBackupSettings();
        
    } catch (error) {
        console.error('Error loading backup data:', error);
        showToast('Failed to load backup data', 'error');
    }
}

// Update backup list
function updateBackupList() {
    const container = document.getElementById('backup-list');
    if (!container) return;
    
    container.innerHTML = '';
    
    if (backupsData.length === 0) {
        container.innerHTML = `
            <div class="text-center py-8">
                <i class="fas fa-database text-4xl text-gray-300 dark:text-gray-600 mb-4"></i>
                <p class="text-gray-500 dark:text-gray-400">No backups available</p>
            </div>
        `;
        return;
    }
    
    const sortedBackups = backupsData.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
    
    sortedBackups.slice(0, 10).forEach(backup => {
        const backupItem = createBackupItem(backup);
        container.appendChild(backupItem);
    });
}

// Create backup item
function createBackupItem(backup) {
    const item = document.createElement('div');
    item.className = 'flex items-center justify-between p-3 border border-gray-200 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors';
    
    const date = new Date(backup.created_at);
    const formattedDate = date.toLocaleDateString();
    const formattedTime = date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
    
    item.innerHTML = `
        <div class="flex-1">
            <p class="text-sm font-medium text-gray-900 dark:text-white">
                ${backup.description || 'Automatic Backup'}
            </p>
            <p class="text-xs text-gray-500 dark:text-gray-400">
                ${formattedDate} at ${formattedTime}
            </p>
            <p class="text-xs text-gray-400 dark:text-gray-500">
                Size: ${formatFileSize(backup.file_size)} | ${backup.tables_count} tables
            </p>
        </div>
        <div class="flex space-x-2">
            <button onclick="downloadBackup('${backup.filename}')" 
                    class="text-blue-600 hover:text-blue-800 dark:text-blue-400" 
                    title="Download">
                <i class="fas fa-download"></i>
            </button>
            <button onclick="restoreBackup('${backup.filename}')" 
                    class="text-green-600 hover:text-green-800 dark:text-green-400" 
                    title="Restore">
                <i class="fas fa-undo"></i>
            </button>
            <button onclick="deleteBackup('${backup.filename}')" 
                    class="text-red-600 hover:text-red-800 dark:text-red-400" 
                    title="Delete">
                <i class="fas fa-trash"></i>
            </button>
        </div>
    `;
    
    return item;
}

// Update backup settings
function updateBackupSettings() {
    const container = document.getElementById('backup-settings');
    if (!container) return;
    
    container.innerHTML = `
        <div class="space-y-4">
            <div class="flex items-center justify-between">
                <div>
                    <label class="block text-sm font-medium text-gray-700 dark:text-gray-300">Automatic Backups</label>
                    <p class="text-xs text-gray-500 dark:text-gray-400">Daily automatic database backups</p>
                </div>
                <label class="relative inline-flex items-center cursor-pointer">
                    <input type="checkbox" checked class="sr-only peer"
                           onchange="toggleAutoBackup(this.checked)">
                    <div class="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 dark:peer-focus:ring-blue-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-blue-600"></div>
                </label>
            </div>
            
            <div>
                <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Retention Days</label>
                <input type="number" value="30" min="1" max="365" 
                       class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                       onchange="updateRetentionDays(this.value)">
                <p class="text-xs text-gray-500 dark:text-gray-400 mt-1">Keep backups for this many days</p>
            </div>
            
            <div>
                <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Backup Description</label>
                <input type="text" id="backup-description" placeholder="Manual backup description" 
                       class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white">
            </div>
            
            <div class="grid grid-cols-2 gap-3">
                <button onclick="createManualBackup()" 
                        class="bg-green-600 hover:bg-green-700 text-white py-2 rounded-lg transition-colors text-sm">
                    <i class="fas fa-plus mr-2"></i>Create Backup
                </button>
                <button onclick="cleanupOldBackups()" 
                        class="bg-orange-600 hover:bg-orange-700 text-white py-2 rounded-lg transition-colors text-sm">
                    <i class="fas fa-broom mr-2"></i>Cleanup Old
                </button>
            </div>
        </div>
    `;
}

// Format file size
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// Create backup
async function createBackup() {
    createManualBackup();
}

// Create manual backup
async function createManualBackup() {
    const description = document.getElementById('backup-description')?.value || 'Manual backup';
    
    try {
        showToast('Creating backup...', 'info');
        
        const response = await fetch('/api/backup/create', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ description })
        });
        
        if (!response.ok) {
            throw new Error('Failed to create backup');
        }
        
        const result = await response.json();
        showToast('Backup created successfully', 'success');
        
        // Reload backup list
        await loadBackupData();
        
        // Clear description field
        const descInput = document.getElementById('backup-description');
        if (descInput) descInput.value = '';
        
    } catch (error) {
        console.error('Error creating backup:', error);
        showToast('Failed to create backup', 'error');
    }
}

// Download backup
async function downloadBackup(filename) {
    try {
        const response = await fetch(`/api/backup/download/${filename}`);
        if (!response.ok) {
            throw new Error('Failed to download backup');
        }
        
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        
        showToast('Backup downloaded', 'success');
        
    } catch (error) {
        console.error('Error downloading backup:', error);
        showToast('Failed to download backup', 'error');
    }
}

// Restore backup
async function restoreBackup(filename) {
    if (!confirm(`Are you sure you want to restore from backup "${filename}"? This will overwrite all current data and cannot be undone.`)) {
        return;
    }
    
    try {
        showToast('Restoring backup...', 'info');
        
        const response = await fetch(`/api/backup/restore/${filename}`, {
            method: 'POST'
        });
        
        if (!response.ok) {
            throw new Error('Failed to restore backup');
        }
        
        showToast('Backup restored successfully', 'success');
        
        // Refresh the page to reflect restored data
        setTimeout(() => {
            window.location.reload();
        }, 2000);
        
    } catch (error) {
        console.error('Error restoring backup:', error);
        showToast('Failed to restore backup', 'error');
    }
}

// Delete backup
async function deleteBackup(filename) {
    if (!confirm(`Are you sure you want to delete backup "${filename}"? This action cannot be undone.`)) {
        return;
    }
    
    try {
        const response = await fetch(`/api/backup/delete/${filename}`, {
            method: 'DELETE'
        });
        
        if (!response.ok) {
            throw new Error('Failed to delete backup');
        }
        
        showToast('Backup deleted successfully', 'success');
        await loadBackupData();
        
    } catch (error) {
        console.error('Error deleting backup:', error);
        showToast('Failed to delete backup', 'error');
    }
}

// Toggle auto backup
async function toggleAutoBackup(enabled) {
    try {
        const response = await fetch('/api/backup/settings', {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ auto_backup: enabled })
        });
        
        if (!response.ok) {
            throw new Error('Failed to update auto backup setting');
        }
        
        showToast(`Auto backup ${enabled ? 'enabled' : 'disabled'}`, 'success');
        
    } catch (error) {
        console.error('Error updating auto backup:', error);
        showToast('Failed to update auto backup setting', 'error');
    }
}

// Update retention days
async function updateRetentionDays(days) {
    try {
        const response = await fetch('/api/backup/settings', {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ retention_days: parseInt(days) })
        });
        
        if (!response.ok) {
            throw new Error('Failed to update retention setting');
        }
        
        showToast('Retention period updated', 'success');
        
    } catch (error) {
        console.error('Error updating retention:', error);
        showToast('Failed to update retention setting', 'error');
    }
}

// Cleanup old backups
async function cleanupOldBackups() {
    if (!confirm('Are you sure you want to delete all expired backups? This action cannot be undone.')) {
        return;
    }
    
    try {
        const response = await fetch('/api/backup/cleanup', {
            method: 'POST'
        });
        
        if (!response.ok) {
            throw new Error('Failed to cleanup backups');
        }
        
        const result = await response.json();
        showToast(`Cleaned up ${result.deleted_count} old backups`, 'success');
        await loadBackupData();
        
    } catch (error) {
        console.error('Error cleaning up backups:', error);
        showToast('Failed to cleanup backups', 'error');
    }
}

// Make functions available globally
window.loadBackupData = loadBackupData;
window.createBackup = createBackup;
window.createManualBackup = createManualBackup;
window.downloadBackup = downloadBackup;
window.restoreBackup = restoreBackup;
window.deleteBackup = deleteBackup;
window.toggleAutoBackup = toggleAutoBackup;
window.updateRetentionDays = updateRetentionDays;
window.cleanupOldBackups = cleanupOldBackups;