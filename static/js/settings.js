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
        updateBotSettings(settings.discord_bot || {});
        updateRatingSettings(settings.rating_system || {});
        updateNotificationSettings(settings.notifications || {});
        
    } catch (error) {
        console.error('Error loading settings data:', error);
        showToast('Не удалось загрузить настройки', 'error');
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
                <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Максимум серверов</label>
                <input type="number" value="${botSettings.max_servers || 8}" min="1" max="20" 
                       class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                       onchange="updateBotSetting('max_servers', this.value)">
                <p class="text-xs text-gray-500 dark:text-gray-400 mt-1">Максимальное количество серверов для мониторинга</p>
            </div>
            

            <div class="flex items-center justify-between">
                <div>
                    <label class="block text-sm font-medium text-gray-700 dark:text-gray-300">Мониторинг включен</label>
                    <p class="text-xs text-gray-500 dark:text-gray-400">Отслеживание активности кураторов</p>
                </div>
                <label class="relative inline-flex items-center cursor-pointer">
                    <input type="checkbox" ${botSettings.monitoring_enabled ? 'checked' : ''} class="sr-only peer"
                           onchange="updateBotSetting('monitoring_enabled', this.checked)">
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

// Update notification settings display
function updateNotificationSettings(notificationSettings) {
    const container = document.getElementById('notification-settings');
    if (!container) return;
    
    container.innerHTML = `
        <div class="space-y-4">
            <div>
                <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Время до напоминания куратору (секунды)</label>
                <input type="number" value="${notificationSettings.curator_reminder_time || 300}" min="5" max="3600" 
                       class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                       onchange="updateGlobalReminderTime(this.value)">
                <p class="text-xs text-gray-500 dark:text-gray-400 mt-1">Время ожидания ответа куратора перед напоминанием</p>
            </div>
            
            <div class="flex items-center justify-between">
                <div>
                    <label class="block text-sm font-medium text-gray-700 dark:text-gray-300">Автонапоминание</label>
                    <p class="text-xs text-gray-500 dark:text-gray-400">Повторять напоминание через то же время</p>
                </div>
                <label class="relative inline-flex items-center cursor-pointer">
                    <input type="checkbox" ${notificationSettings.auto_reminder ? 'checked' : ''} class="sr-only peer"
                           onchange="updateGlobalAutoReminder(this.checked)">
                    <div class="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 dark:peer-focus:ring-blue-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-blue-600"></div>
                </label>
            </div>
            
            <div class="flex items-center justify-between">
                <div>
                    <label class="block text-sm font-medium text-gray-700 dark:text-gray-300">Email уведомления</label>
                    <p class="text-xs text-gray-500 dark:text-gray-400">Отправка уведомлений на email</p>
                </div>
                <label class="relative inline-flex items-center cursor-pointer">
                    <input type="checkbox" ${notificationSettings.email_notifications ? 'checked' : ''} class="sr-only peer"
                           onchange="updateNotificationSetting('email_notifications', this.checked)">
                    <div class="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 dark:peer-focus:ring-blue-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-blue-600"></div>
                </label>
            </div>
        </div>
    `;
}

// Update bot setting
async function updateBotSetting(key, value) {
    try {
        const response = await fetch('/api/settings', {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ 
                discord_bot: { [key]: value }
            })
        });
        
        if (!response.ok) {
            throw new Error('Failed to update setting');
        }
        
        showToast('Настройка обновлена', 'success');
        
    } catch (error) {
        console.error('Error updating setting:', error);
        showToast('Ошибка при обновлении настройки', 'error');
    }
}

// Update notification setting
async function updateNotificationSetting(key, value) {
    try {
        const response = await fetch('/api/settings', {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ 
                notifications: { [key]: value }
            })
        });
        
        if (!response.ok) {
            throw new Error('Failed to update notification setting');
        }
        
        showToast('Настройка уведомлений обновлена', 'success');
        
    } catch (error) {
        console.error('Error updating notification setting:', error);
        showToast('Ошибка при обновлении настройки уведомлений', 'error');
    }
}

// Update rating point
async function updateRatingPoint(type, points) {
    try {
        const response = await fetch('/api/settings', {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ 
                rating_system: { 
                    points: { [type]: parseInt(points) }
                }
            })
        });
        
        if (!response.ok) {
            throw new Error('Failed to update rating points');
        }
        
        showToast('Очки рейтинга обновлены', 'success');
        
    } catch (error) {
        console.error('Error updating rating points:', error);
        showToast('Ошибка при обновлении очков рейтинга', 'error');
    }
}

// Save all settings
async function saveSettings() {
    showToast('Settings saved successfully', 'success');
}

// Update global reminder time for all servers
async function updateGlobalReminderTime(seconds) {
    try {
        const response = await fetch('/api/servers');
        const servers = await response.json();
        
        // Update all servers
        for (const server of servers) {
            await fetch(`/api/servers/${server.id}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ reminder_interval_seconds: parseInt(seconds) })
            });
        }
        
        showToast('Время напоминания обновлено для всех серверов', 'success');
        
    } catch (error) {
        console.error('Error updating reminder time:', error);
        showToast('Ошибка при обновлении времени напоминания', 'error');
    }
}

// Update global auto-reminder setting for all servers
async function updateGlobalAutoReminder(enabled) {
    try {
        const response = await fetch('/api/servers');
        const servers = await response.json();
        
        // Update all servers
        for (const server of servers) {
            await fetch(`/api/servers/${server.id}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ auto_reminder_enabled: enabled })
            });
        }
        
        showToast('Настройка автонапоминаний обновлена для всех серверов', 'success');
        
    } catch (error) {
        console.error('Error updating auto-reminder:', error);
        showToast('Ошибка при обновлении настройки автонапоминаний', 'error');
    }
}

// Make functions available globally
window.loadSettingsData = loadSettingsData;
window.updateBotSetting = updateBotSetting;
window.updateNotificationSetting = updateNotificationSetting;
window.updateRatingPoint = updateRatingPoint;
window.updateGlobalReminderTime = updateGlobalReminderTime;
window.updateGlobalAutoReminder = updateGlobalAutoReminder;
window.saveSettings = saveSettings;