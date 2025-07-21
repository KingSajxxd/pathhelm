# mock_service.py
from socket import if_indextoname
from flask import Flask, request

app = Flask(__name__)

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')

def catch_all(path):
    print(f"Mock service received request for path: /{path}")
    return{
        "message": "Hello from the mock backend!",
        "requested_path": f"/{path}",
        "headers_received": dict(request.headers)
    }

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
