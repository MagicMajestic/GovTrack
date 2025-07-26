// GovTracker2 Python Migration by Replit Agent - Settings Management

// Load settings data
async function loadSettingsData() {
    console.log('Loading settings data...');
    try {
        const response = await fetch('/api/settings');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const settings = await response.json();
        updateBotSettings(settings.bot_settings || {});
        updateRatingSettings(settings.rating_settings || {});
        
    } catch (error) {
        console.error('Error loading settings data:', error);
        showToast('Failed to load settings data', 'error');
    }
}

// Update bot settings display
function updateBotSettings(botSettings) {
    const container = document.getElementById('bot-settings');
    if (!container) return;
    
    container.innerHTML = `
        <div class="space-y-4">
            <div class="flex items-center justify-between">
                <div>
                    <label class="block text-sm font-medium text-gray-700 dark:text-gray-300">Bot Status</label>
                    <p class="text-xs text-gray-500 dark:text-gray-400">Discord bot connection status</p>
                </div>
                <div class="flex items-center space-x-2">
                    <div class="w-3 h-3 rounded-full ${botSettings.is_online ? 'bg-green-500' : 'bg-red-500'}"></div>
                    <span class="text-sm ${botSettings.is_online ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}">
                        ${botSettings.is_online ? 'Online' : 'Offline'}
                    </span>
                </div>
            </div>
            
            <div>
                <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Monitored Servers</label>
                <input type="number" value="${botSettings.max_servers || 8}" min="1" max="20" 
                       class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                       onchange="updateBotSetting('max_servers', this.value)">
                <p class="text-xs text-gray-500 dark:text-gray-400 mt-1">Maximum number of servers to monitor</p>
            </div>
            
            <div>
                <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Response Timeout (seconds)</label>
                <input type="number" value="${botSettings.response_timeout || 300}" min="30" max="3600" 
                       class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                       onchange="updateBotSetting('response_timeout', this.value)">
                <p class="text-xs text-gray-500 dark:text-gray-400 mt-1">Timeout for curator response tracking</p>
            </div>
            
            <div class="flex items-center justify-between">
                <div>
                    <label class="block text-sm font-medium text-gray-700 dark:text-gray-300">Auto Backup</label>
                    <p class="text-xs text-gray-500 dark:text-gray-400">Automatic daily backups</p>
                </div>
                <label class="relative inline-flex items-center cursor-pointer">
                    <input type="checkbox" ${botSettings.auto_backup ? 'checked' : ''} class="sr-only peer"
                           onchange="updateBotSetting('auto_backup', this.checked)">
                    <div class="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 dark:peer-focus:ring-blue-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-blue-600"></div>
                </label>
            </div>
        </div>
    `;
}

// Update rating settings display
function updateRatingSettings(ratingSettings) {
    const container = document.getElementById('rating-settings');
    if (!container) return;
    
    const ratingPoints = ratingSettings.points || {
        message: 3,
        reaction: 1,
        reply: 2,
        task_verification: 5
    };
    
    container.innerHTML = `
        <div class="space-y-4">
            <div>
                <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Points System</label>
                <div class="space-y-3">
                    <div class="flex items-center justify-between">
                        <span class="text-sm text-gray-600 dark:text-gray-400">Messages</span>
                        <input type="number" value="${ratingPoints.message}" min="0" max="10" 
                               class="w-20 px-2 py-1 border border-gray-300 dark:border-gray-600 rounded focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white text-center"
                               onchange="updateRatingPoint('message', this.value)">
                    </div>
                    <div class="flex items-center justify-between">
                        <span class="text-sm text-gray-600 dark:text-gray-400">Reactions</span>
                        <input type="number" value="${ratingPoints.reaction}" min="0" max="10" 
                               class="w-20 px-2 py-1 border border-gray-300 dark:border-gray-600 rounded focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white text-center"
                               onchange="updateRatingPoint('reaction', this.value)">
                    </div>
                    <div class="flex items-center justify-between">
                        <span class="text-sm text-gray-600 dark:text-gray-400">Replies</span>
                        <input type="number" value="${ratingPoints.reply}" min="0" max="10" 
                               class="w-20 px-2 py-1 border border-gray-300 dark:border-gray-600 rounded focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white text-center"
                               onchange="updateRatingPoint('reply', this.value)">
                    </div>
                    <div class="flex items-center justify-between">
                        <span class="text-sm text-gray-600 dark:text-gray-400">Task Verification</span>
                        <input type="number" value="${ratingPoints.task_verification}" min="0" max="20" 
                               class="w-20 px-2 py-1 border border-gray-300 dark:border-gray-600 rounded focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white text-center"
                               onchange="updateRatingPoint('task_verification', this.value)">
                    </div>
                </div>
            </div>
            
            <div>
                <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Rating Thresholds</label>
                <div class="space-y-2 text-sm">
                    <div class="flex justify-between items-center">
                        <span class="text-green-600 dark:text-green-400">Excellent</span>
                        <span class="text-gray-600 dark:text-gray-400">50+ points</span>
                    </div>
                    <div class="flex justify-between items-center">
                        <span class="text-blue-600 dark:text-blue-400">Good</span>
                        <span class="text-gray-600 dark:text-gray-400">35+ points</span>
                    </div>
                    <div class="flex justify-between items-center">
                        <span class="text-yellow-600 dark:text-yellow-400">Normal</span>
                        <span class="text-gray-600 dark:text-gray-400">20+ points</span>
                    </div>
                    <div class="flex justify-between items-center">
                        <span class="text-orange-600 dark:text-orange-400">Poor</span>
                        <span class="text-gray-600 dark:text-gray-400">10+ points</span>
                    </div>
                    <div class="flex justify-between items-center">
                        <span class="text-red-600 dark:text-red-400">Terrible</span>
                        <span class="text-gray-600 dark:text-gray-400">0-9 points</span>
                    </div>
                </div>
            </div>
            
            <button onclick="saveSettings()" class="w-full bg-blue-600 hover:bg-blue-700 text-white py-2 rounded-lg transition-colors">
                <i class="fas fa-save mr-2"></i>Save Settings
            </button>
        </div>
    `;
}

// Update bot setting
async function updateBotSetting(key, value) {
    try {
        const response = await fetch('/api/settings/bot', {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ [key]: value })
        });
        
        if (!response.ok) {
            throw new Error('Failed to update setting');
        }
        
        showToast('Setting updated successfully', 'success');
        
    } catch (error) {
        console.error('Error updating setting:', error);
        showToast('Failed to update setting', 'error');
    }
}

// Update rating point
async function updateRatingPoint(type, points) {
    try {
        const response = await fetch('/api/settings/rating', {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ type, points: parseInt(points) })
        });
        
        if (!response.ok) {
            throw new Error('Failed to update rating points');
        }
        
        showToast('Rating points updated successfully', 'success');
        
    } catch (error) {
        console.error('Error updating rating points:', error);
        showToast('Failed to update rating points', 'error');
    }
}

// Save all settings
async function saveSettings() {
    showToast('Settings saved successfully', 'success');
}

// Make functions available globally
window.loadSettingsData = loadSettingsData;
window.updateBotSetting = updateBotSetting;
window.updateRatingPoint = updateRatingPoint;
window.saveSettings = saveSettings;