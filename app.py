from flask import Flask, Response
from flask_socketio import SocketIO, emit
import eventlet
import eventlet.wsgi

eventlet.monkey_patch()

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

@app.route("/")
def index():
    return Response("""
    <!DOCTYPE html>
    <html>
    <head>
      <title>Live G-Ball</title>
      <script src="https://cdn.socket.io/4.0.0/socket.io.min.js"></script>
      <style>
        body { background: #111; color: white; font-family: sans-serif; margin: 0; }
        canvas { background: #222; display: block; margin: auto; }
      </style>
    </head>
    <body>
      <canvas id="gBall" width="600" height="600"></canvas>
      <script>
        const canvas = document.getElementById("gBall");
        const ctx = canvas.getContext("2d");
        const centerX = 300, centerY = 300, radius = 20, sensitivity = 100;
        let xG = 0, yG = 0, xBall = centerX, yBall = centerY;

        const socket = io({ transports: ["websocket"] });
        socket.on("connect", () => console.log("✅ WebSocket connected!"));
        socket.on("g_data", data => {
          xG = data.xG;
          yG = data.yG;
          console.log("Received:", xG, yG);
        });

        function draw() {
          ctx.clearRect(0, 0, 600, 600);
          xBall = xBall * 0.85 + (centerX + yG * sensitivity) * 0.15;
          yBall = yBall * 0.85 + (centerY - xG * sensitivity) * 0.15;

          ctx.beginPath();
          ctx.arc(centerX, centerY, 200, 0, 2 * Math.PI);
          ctx.strokeStyle = "#999"; ctx.stroke();

          ctx.beginPath();
          ctx.arc(xBall, yBall, radius, 0, 2 * Math.PI);
          ctx.fillStyle = (xG > 0.1) ? "red" : "lime";
          ctx.fill();

          ctx.fillStyle = "white";
          ctx.fillText(`Accel: ${xG.toFixed(2)}g`, 20, 30);
          ctx.fillText(`Lateral: ${yG.toFixed(2)}g`, 20, 50);
          requestAnimationFrame(draw);
        }

        draw();
      </script>
    </body>
    </html>
    """, mimetype='text/html')

@socketio.on('esp_data')
def handle_esp_data(data):
    print("Received from ESP32:", data)
    emit("g_data", data, broadcast=True)

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000)
