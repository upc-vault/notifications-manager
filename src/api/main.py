from flask import Flask, request
from pydantic import TypeAdapter
from typing import List
from model.notification import Notification
import redis
import uuid

app = Flask(__name__)
pool = redis.ConnectionPool(host='localhost', port=6379, db=0)
r = redis.Redis(connection_pool=pool)
scope = "notifications"
version = "v0"
api = "send-notifications"


@app.route(f'/{scope}/{version}/{api}', methods=['POST'])
def sendNotifications():
    if request.get_json() is None:
        print("Error")

    notifications_adapter = TypeAdapter(List[Notification])
    notifications = notifications_adapter.validate_python(request.get_json())

    for notification in notifications:
        notification.id = str(uuid.uuid4())
        print(notification)
    return 'hello'


if __name__ == '__main__':
    app.run(debug=True)
