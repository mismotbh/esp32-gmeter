from flask import Flask, render_template_string, request
from simple_websocket import Server, ConnectionClosed
import threading

app = Flask(__name__)
clients = []

HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
  <title>Live G-Ball</title>
  <style>
    body { background: #111; margin: 0; overflow: hidden; }
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

    const socket = new WebSocket("wss://" + location.host + "/ws");

    socket.onmessage = function(event) {
      const data = JSON.parse(event.data);
      xG = data.xG;
      yG = data.yG;
    };

    function draw() {
      ctx.clearRect(0, 0, 600, 600);
      xBall = xBall * 0.85 + (centerX + yG * sensitivity) * 0.15;
      yBall = yBall * 0.85 + (centerY - xG * sensitivity) * 0.15;

      ctx.beginPath();
      ctx.arc(centerX, centerY, 200, 0, 2 * Math.PI);
      ctx.strokeStyle = "#888"; ctx.stroke();

      ctx.beginPath();
      ctx.arc(xBall, yBall, radius, 0, 2 * Math.PI);
      ctx.fillStyle = (xG > 0.1) ? "red" : "lime";
      ctx.fill();

      ctx.fillStyle = "#fff";
      ctx.fillText("Accel: " + xG.toFixed(2) + "g", 20, 30);
      ctx.fillText("Lateral: " + yG.toFixed(2) + "g", 20, 50);

      requestAnimationFrame(draw);
    }

    draw();
  </script>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(HTML_PAGE)

@app.route("/ws")
def ws_route():
    def run_ws():
        ws = Server(request.environ)
        clients.append(ws)
        try:
            while True:
                msg = ws.receive()
                for client in clients:
                    if client != ws:
                        client.send(msg)
        except ConnectionClosed:
            clients.remove(ws)
    threading.Thread(target=run_ws).start()
    return ""

if __name__ == "__main__":
    from werkzeug.serving import run_simple
    run_simple("0.0.0.0", 5000, app, threaded=True, ssl_context=None)
