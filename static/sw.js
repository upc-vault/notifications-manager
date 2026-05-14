// Service Worker for Web Push Notifications
// Version: 2.0 - Click tracking enabled
const SW_VERSION = '2.0';

self.addEventListener('install', (event) => {
    console.log(`Service Worker v${SW_VERSION} installing...`);
    self.skipWaiting(); // Activate immediately
});

self.addEventListener('activate', (event) => {
    console.log(`Service Worker v${SW_VERSION} activated`);
    event.waitUntil(clients.claim()); // Take control immediately
});

self.addEventListener('push', (event) => {
    console.log('Push event received:', event);
    
    let notificationData = {
        title: 'Notification',
        body: 'You have a new message',
        icon: '/static/images/notification-icon.png',
        badge: '/static/images/badge.png',
        tag: 'default',
        requireInteraction: false,
        data: {
            url: '/'
        }
    };
    
    // Parse notification data if available
    if (event.data) {
        try {
            const payload = event.data.json();
            console.log('Notification payload:', payload);
            
            notificationData = {
                title: payload.title || notificationData.title,
                body: payload.body || notificationData.body,
                icon: payload.icon || notificationData.icon,
                badge: payload.badge || notificationData.badge,
                tag: payload.tag || notificationData.tag,
                requireInteraction: payload.requireInteraction || false,
                silent: payload.silent || false,
                data: payload.data || notificationData.data,
                ...(payload.image && { image: payload.image }),
                ...(payload.actions && { actions: payload.actions })
            };
        } catch (error) {
            console.error('Failed to parse notification payload:', error);
        }
    }
    
    // Show notification
    const promiseChain = self.registration.showNotification(
        notificationData.title,
        {
            body: notificationData.body,
            icon: notificationData.icon,
            badge: notificationData.badge,
            tag: notificationData.tag,
            requireInteraction: notificationData.requireInteraction,
            silent: notificationData.silent,
            data: notificationData.data,
            ...(notificationData.image && { image: notificationData.image }),
            ...(notificationData.actions && { actions: notificationData.actions })
        }
    );
    
    event.waitUntil(promiseChain);
});

self.addEventListener('notificationclick', (event) => {
    console.log(`[SW v${SW_VERSION}] 🖱️ Notification clicked!`);
    console.log(`[SW v${SW_VERSION}] 📦 Notification:`, event.notification);
    console.log(`[SW v${SW_VERSION}] 📦 Notification data:`, event.notification.data);
    
    event.notification.close();
    
    // Get log_id and URL from notification data
    const logId = event.notification.data?.log_id;
    const urlToOpen = event.notification.data?.url || '/';
    
    console.log(`[SW v${SW_VERSION}] 🔍 Extracted log_id:`, logId);
    console.log(`[SW v${SW_VERSION}] 🔗 URL to open:`, urlToOpen);
    
    // If we have a log_id, append it as a query parameter for tracking
    let finalUrl = urlToOpen;
    if (logId) {
        try {
            const url = new URL(urlToOpen, self.location.origin);
            url.searchParams.set('track_click', logId);
            finalUrl = url.toString();
            console.log(`[SW v${SW_VERSION}] 📍 Final URL with tracking:`, finalUrl);
        } catch (err) {
            console.error(`[SW v${SW_VERSION}] ❌ Error building URL:`, err);
        }
    } else {
        console.warn(`[SW v${SW_VERSION}] ⚠️ No log_id found in notification data!`);
    }
    
    // Open or focus a window with the tracking URL
    const openPromise = self.clients.matchAll({ 
        type: 'window', 
        includeUncontrolled: true 
    }).then((clientList) => {
        console.log(`[SW v${SW_VERSION}] 👥 Found ${clientList.length} clients`);
        
        // Try to find an existing window to focus
        for (const client of clientList) {
            // If we have a log_id, send a message to track it
            if (logId) {
                console.log(`[SW v${SW_VERSION}] 📤 Sending TRACK_CLICK message to client:`, client.url);
                client.postMessage({
                    type: 'TRACK_CLICK',
                    logId: logId
                });
            }
            
            // Focus the client if it matches
            if ('focus' in client) {
                console.log(`[SW v${SW_VERSION}] 🎯 Focusing existing client:`, client.url);
                return client.focus();
            }
        }
        
        // No matching client found, open new window
        if (self.clients.openWindow) {
            console.log(`[SW v${SW_VERSION}] 🆕 Opening new window:`, finalUrl);
            return self.clients.openWindow(finalUrl);
        }
    }).catch(err => {
        console.error(`[SW v${SW_VERSION}] ❌ Error in notification click handler:`, err);
    });
    
    event.waitUntil(openPromise);
});

self.addEventListener('notificationclose', (event) => {
    console.log('Notification closed:', event.notification);
    
    // Optional: Send analytics event
    // You could track which notifications users close without clicking
});

// Handle push subscription change (e.g., if subscription expires)
self.addEventListener('pushsubscriptionchange', (event) => {
    console.log('Push subscription changed');
    
    event.waitUntil(
        self.registration.pushManager.subscribe({
            userVisibleOnly: true,
            applicationServerKey: event.oldSubscription.options.applicationServerKey
        })
        .then((subscription) => {
            console.log('Re-subscribed:', subscription);
            
            // Send new subscription to server
            return fetch('http://localhost:8080/api/v1/webpush/subscribe', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    user_id: 'resubscribe',
                    subscription: subscription.toJSON()
                })
            });
        })
        .catch((error) => {
            console.error('Re-subscription failed:', error);
        })
    );
});
