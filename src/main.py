from flask import Flask, request
from model.notification import Notification
from pydantic import TypeAdapter

app = Flask(__name__)


@app.route('/communications/v0/notifications', methods=['POST'])
def sendNotification():
    notifications_adapter = TypeAdapter(list[Notification])
    notifications = notifications_adapter.validate_json(request.body)
    print(notifications)


if __name__ == '__main__':
    app.run(debug=True)
