Notifications data must contain a reward for each notification the user has tapped. Therefore a is_tapped column is mandatory. We also have to know the user the notification was sent, the template identification, channel, the application aimed to send it and also auditory fields such as creation_date, creation_user, user_audit_id and audit_date. Then our notifications_log table must see as the following:

``` JSON
{
    "notifications": [
        {
            "id": "5D8EDF32-35F9-432E-979A-1AC87BD8227B",
            "templateId": "FFA4A93F-0250-49BC-BB76-1D0D7293AC39",
            "sender": {
                "id": "087654321",
                "type": "customer | non-customer | employee"
            },
            "receiver": {
                "id": "008765432",
                "type": "customer | non-customer | employee"
            },
            "channelCode": "12345678",
            "wasTapped": true | false,
            "wasSent": true | false,
            "sendingTime": "2025-12-24 14:15:16",
            "scheduledTime": "2025-12-24 14:15:16",
            "attachments": [
                {
                    "id": "41411E43-5076-439F-BE5F-A1AD409942A2"
                }
            ],
            "data": [
                {
                    "key": "name",
                    "value": "Juancito"
                }
            ],
            "creationDate": "2025-12-24 14:15:16",
            "creationUser": "u202324341",
            "userAuditId": "2025-12-24 14:15:16",
            "auditDate": "u202324341"
        }
    ]
}
```

Now we've defined this short data model (which may have changes along time) now let's get into the ML algorithm and how it should work.

First, as we have a wasTapped key, it may work for our reward function. The amount of taps for a given template and user is denoted as T_tu and the total amount of taps as T. Then our calculation of user feedback for that notification is as follows:
