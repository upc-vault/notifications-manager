// Service Worker for Web Push Notifications

self.addEventListener('install', event => {
    console.log('Service Worker installed');
    self.skipWaiting();
});

self.addEventListener('activate', event => {
    console.log('Service Worker activated');
    event.waitUntil(clients.claim());
});

// Handle push notification
self.addEventListener('push', event => {
    console.log('Push notification received:', event);
    
    let notificationData = {
        title: 'Bank Notification',
        body: 'You have a new notification',
        icon: '/static/icon.png',
        badge: '/static/badge.png',
        tag: 'notification-' + Date.now(),
        data: {
            url: '/',
            timestamp: new Date().toISOString()
        }
    };

    // Parse notification data from push event
    if (event.data) {
        try {
            const data = event.data.json();
            notificationData = {
                title: data.title || notificationData.title,
                body: data.body || notificationData.body,
                icon: data.icon || notificationData.icon,
                badge: data.badge || notificationData.badge,
                tag: data.tag || notificationData.tag,
                data: data.data || notificationData.data,
                requireInteraction: data.requireInteraction || false,
                silent: data.silent || false
            };
        } catch (error) {
            console.error('Error parsing push data:', error);
        }
    }

    // Show notification
    event.waitUntil(
        self.registration.showNotification(notificationData.title, {
            body: notificationData.body,
            icon: notificationData.icon,
            badge: notificationData.badge,
            tag: notificationData.tag,
            data: notificationData.data,
            requireInteraction: notificationData.requireInteraction,
            silent: notificationData.silent,
            vibrate: [200, 100, 200]
        }).then(() => {
            // Notify any open clients
            return self.clients.matchAll({ type: 'window' });
        }).then(clients => {
            clients.forEach(client => {
                client.postMessage({
                    type: 'notification',
                    notification: {
                        title: notificationData.title,
                        body: notificationData.body,
                        timestamp: notificationData.data.timestamp
                    }
                });
            });
        })
    );
});

// Handle notification click
self.addEventListener('notificationclick', event => {
    console.log('Notification clicked:', event);
    
    const notificationId = event.notification.data?.notification_id;
    const notificationType = event.notification.data?.notification_type;
    
    event.notification.close();

    const urlToOpen = event.notification.data?.url || '/';

    event.waitUntil(
        // Send click feedback to API
        fetch('http://localhost:5000/api/v1/webpush/track-click', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                notification_id: notificationId,
                clicked: true,
                timestamp: new Date().toISOString()
            })
        }).catch(err => console.error('Failed to send click feedback:', err))
        .then(() => {
            // Open or focus window
            return clients.matchAll({ type: 'window', includeUncontrolled: true });
        })
        .then(clientList => {
            // Check if there's already a window open
            for (let client of clientList) {
                if (client.url === urlToOpen && 'focus' in client) {
                    return client.focus();
                }
            }
            // Open new window
            if (clients.openWindow) {
                return clients.openWindow(urlToOpen);
            }
        })
    );
});

// Handle notification close
self.addEventListener('notificationclose', event => {
    console.log('Notification closed:', event);
});
