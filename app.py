from flask import Flask, render_template_string
from flask_sock import Sock

app = Flask(__name__)
sock = Sock(app)
clients = set()

HTML = """
<!DOCTYPE html>
<html>
<head>
  <title>Live G-Ball</title>
  <style>
    body { margin: 0; background: #111; }
    canvas { background: #222; display: block; margin: auto; }
  </style>
</head>
<body>
  <canvas id="gBall" width="600" height="600"></canvas>
  <script>
    const canvas = document.getElementById("gBall");
    const ctx = canvas.getContext("2d");
    const centerX = 300, centerY = 300, radius = 20, sensitivity = 100;
    let xG = 0, yG = 0;

    const ws = new WebSocket("wss://" + location.host + "/ws");

    ws.onmessage = function(event) {
      const data = JSON.parse(event.data);
      xG = data.xG;
      yG = data.yG;
    };

    function draw() {
      ctx.clearRect(0, 0, 600, 600);

      const xBall = centerX + yG * sensitivity;
      const yBall = centerY - xG * sensitivity;

      ctx.beginPath();
      ctx.arc(centerX, centerY, 200, 0, 2 * Math.PI);
      ctx.strokeStyle = "#999"; ctx.stroke();

      ctx.beginPath();
      ctx.arc(xBall, yBall, radius, 0, 2 * Math.PI);
      ctx.fillStyle = (xG > 0.1) ? "red" : "lime";
      ctx.fill();

      ctx.fillStyle = "white";
      ctx.fillText("Accel: " + xG.toFixed(2), 20, 30);
      ctx.fillText("Lateral: " + yG.toFixed(2), 20, 50);

      requestAnimationFrame(draw);
    }
    draw();
  </script>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(HTML)

@sock.route("/ws")
def websocket(ws):
    clients.add(ws)
    try:
        while True:
            data = ws.receive()
            if data:
                for client in list(clients):
                    if client != ws:
                        try:
                            client.send(data)
                        except:
                            clients.discard(client)
    except:
        clients.discard(ws)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
