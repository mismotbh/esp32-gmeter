
from flask import Flask, render_template_string, request
from flask_socketio import SocketIO, emit
import eventlet

eventlet.monkey_patch()

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

latest_data = {"xG": 0.0, "yG": 0.0}

@app.route("/")
def index():
    return render_template_string("""
<!DOCTYPE html>
<html>
<head>
    <title>Night Owl Racing G-Meter</title>
    <style>
        body {
            background-color: black;
            color: yellow;
            font-family: 'Arial', sans-serif;
            text-align: center;
        }
        #circle {
            margin: 30px auto;
            width: 300px;
            height: 300px;
            border: 4px solid yellow;
            border-radius: 50%;
            position: relative;
        }
        #dot {
            width: 20px;
            height: 20px;
            background-color: yellow;
            border-radius: 50%;
            position: absolute;
            top: 140px;
            left: 140px;
        }
        h1 {
            color: yellow;
        }
    </style>
</head>
<body>
    <h1>Night Owl Racing</h1>
    <div id="circle">
        <div id="dot"></div>
    </div>
    <h2>Live G-Forces</h2>
    <p id="xG">X: 0.00</p>
    <p id="yG">Y: 0.00</p>

    <script src="https://cdn.socket.io/4.0.0/socket.io.min.js"></script>
    <script>
        var socket = io();
        socket.on('gforce', function(data) {
            document.getElementById("xG").innerText = "X: " + data.xG.toFixed(2);
            document.getElementById("yG").innerText = "Y: " + data.yG.toFixed(2);

            const dot = document.getElementById("dot");
            let offsetX = data.xG * 100;
            let offsetY = -data.yG * 100;
            dot.style.left = 140 + offsetX + "px";
            dot.style.top = 140 + offsetY + "px";
        });
    </script>
</body>
</html>
""")  # End of template

@app.route("/update", methods=["POST"])
def update():
    global latest_data
    json_data = request.get_json()
    latest_data = json_data
    socketio.emit('gforce', latest_data)
    return "OK"

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000)
