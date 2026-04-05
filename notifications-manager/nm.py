from flask import Flask, request
from pydantic import TypeAdapter
from model.notification import Notification
import oracledb
import redis
import uuid

app = Flask(__name__)
pool = redis.ConnectionPool(
    host='localhost',
    port=6379,
    db=0
)
r = redis.Redis(connection_pool=pool)
scope = "notifications"
version = "v0"
api = "send-notification"


@app.route(f'/{scope}/{version}/{api}', methods=['POST'])
def sendNotifications():
    if request.get_json() is None:
        print("Input JSON can't be null or empty")

    notification_adapter = TypeAdapter(Notification)
    notification = notification_adapter.validate_python(request.get_json())
    notification.id = str(uuid.uuid4())
    
    return notification.id


if __name__ == '__main__':
    app.run(debug=True)
