# mock_service.py
from flask import Flask, request, jsonify
import random
import time

app = Flask(__name__)

# simulating a service getting overwhelmed
request_times = []

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')

def catch_all(path):
    global request_times
    current_time = time.time()

    # keeping track of recent records
    request_times = [t for t in request_times if current_time - t < 5] # 5 second window
    request_times.append(current_time)

    # if we get more than 10 requests in 5 seconds, return errors
    if len(request_times) > 10:
        if random.random() < 0.5: # 50% chance of server error
            return jsonify({"error": "Service Overloaded"}), 500
        else: # 50% chance of a client error
            return jsonify({"error": "Invalid request due to high load"}), 400


    # otherwise, succeed
    return jsonify({
        "message": "Hello from the mock backend!",
        "requested_path": f"/{path}",
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
