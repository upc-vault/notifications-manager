from flask import Flask, request
from model.notification import Notification
from pydantic import TypeAdapter
import redis

app = Flask(__name__)


@app.route('/notifications/v0/send-notifications', methods=['POST'])
def sendNotifications():
    notifications_adapter = TypeAdapter(list[Notification])
    notifications = notifications_adapter.validate_json(request.body)
    r = redis.Redis(host='localhost', port=6379, decode_responses=True)


if __name__ == '__main__':
    app.run(debug=True)
