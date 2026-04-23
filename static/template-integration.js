// Template selection enhancement for index.html
// Add this to extend the existing notification system with template support

let availableTemplates = [];

// Load templates when page loads
async function loadAvailableTemplates() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/v1/templates`);
        const allTemplates = await response.json();
        
        // Filter templates that support webpush
        availableTemplates = allTemplates.filter(t => 
            t.channels && t.channels.includes('webpush')
        );
        
        console.log(`Loaded ${availableTemplates.length} WebPush templates`);
        
        // Create template selector if templates exist
        if (availableTemplates.length > 0) {
            createTemplateSelector();
        }
    } catch (error) {
        console.error('Failed to load templates:', error);
    }
}

function createTemplateSelector() {
    const testBtn = document.getElementById('testBtn');
    if (!testBtn || testBtn.dataset.templateSelectorAdded) return;
    
    testBtn.dataset.templateSelectorAdded = 'true';
    
    // Create template selector container
    const selectorHtml = `
        <div id="templateSelectorContainer" style="margin: 15px 0; padding: 15px; background: white; border-radius: 10px; border: 2px solid #e0e0e0;">
            <label style="display: block; margin-bottom: 10px; font-weight: 600; color: #333;">
                📝 Select Template:
            </label>
            <select id="templateDropdown" style="width: 100%; padding: 12px; border: 2px solid #e0e0e0; border-radius: 8px; font-size: 14px; margin-bottom: 10px;">
                <option value="">🧪 Default Test Notification</option>
                ${availableTemplates.map(t => 
                    `<option value="${t.id}">${t.name} (${t.type})</option>`
                ).join('')}
            </select>
            <div id="templatePreviewBox" style="display: none; padding: 12px; background: #f8f9fa; border-radius: 8px; font-size: 13px;">
                <strong id="previewTemplateTitle" style="display: block; margin-bottom: 5px; color: #333;"></strong>
                <span id="previewTemplateBody" style="color: #666;"></span>
            </div>
        </div>
    `;
    
    // Insert before test button
    testBtn.insertAdjacentHTML('beforebegin', selectorHtml);
    
    // Add change handler
    const dropdown = document.getElementById('templateDropdown');
    dropdown.addEventListener('change', onTemplateSelected);
    
    // Update button text
    testBtn.textContent = '🚀 Send Notification';
}

function onTemplateSelected() {
    const dropdown = document.getElementById('templateDropdown');
    const previewBox = document.getElementById('templatePreviewBox');
    const previewTitle = document.getElementById('previewTemplateTitle');
    const previewBody = document.getElementById('previewTemplateBody');
    
    const templateId = dropdown.value;
    
    if (!templateId) {
        previewBox.style.display = 'none';
        return;
    }
    
    const template = availableTemplates.find(t => t.id === templateId);
    if (template) {
        previewTitle.textContent = template.title;
        const bodyText = template.body.substring(0, 150);
        previewBody.textContent = bodyText + (template.body.length > 150 ? '...' : '');
        previewBox.style.display = 'block';
    }
}

// Override sendTestNotification function
const originalSendTestNotification = window.sendTestNotification;
window.sendTestNotification = async function() {
    const dropdown = document.getElementById('templateDropdown');
    const selectedTemplateId = dropdown ? dropdown.value : '';
    
    if (!selectedTemplateId) {
        // Use original function for default notification
        return originalSendTestNotification();
    }
    
    // Send with selected template
    console.log('Sending notification with template:', selectedTemplateId);
    
    try {
        // Get template for display
        const template = availableTemplates.find(t => t.id === selectedTemplateId);
        
        // Example variables - you can make this dynamic later
        const variables = {
            user_name: 'John Doe',
            amount: '$250.00',
            date: new Date().toLocaleDateString(),
            account: '****1234'
        };
        
        const response = await fetch(`${API_BASE_URL}/api/v1/webpush/send-with-template`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                user_id: userId,
                template_id: selectedTemplateId,
                variables: variables
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            showStatus(`✅ Notification sent using "${template.name}" template!`, 'subscribed');
            addNotificationToList({
                title: template.title,
                body: `Template: ${template.name}`,
                timestamp: new Date().toISOString()
            });
        } else {
            showStatus('❌ Failed to send notification: ' + (result.error || 'Unknown error'), 'error');
        }
    } catch (error) {
        console.error('Error sending template notification:', error);
        showStatus('❌ Error: ' + error.message, 'error');
    }
};

// Initialize templates when subscription is successful
const originalSubscribe = window.subscribe;
if (originalSubscribe) {
    window.subscribe = async function() {
        await originalSubscribe();
        await loadAvailableTemplates();
    };
}

// Load templates on page load if already subscribed
window.addEventListener('load', () => {
    setTimeout(async () => {
        const testBtn = document.getElementById('testBtn');
        if (testBtn && !testBtn.classList.contains('hidden')) {
            await loadAvailableTemplates();
        }
    }, 1000);
});
