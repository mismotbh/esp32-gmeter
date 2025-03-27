from flask import Flask, render_template_string, request
from flask_sock import Sock

app = Flask(__name__)
sock = Sock(app)
latest_data = {"xG": 0, "yG": 0}
clients = set()

HTML = """
<!DOCTYPE html>
<html>
<head>
  <title>Live G-Meter</title>
  <style>
    body { margin: 0; background: #111; color: white; font-family: sans-serif; text-align: center; }
    canvas { background: #222; display: block; margin: 20px auto; }
    .stats { margin-top: 20px; font-size: 1.2em; }
  </style>
</head>
<body>
  <canvas id="gBall" width="600" height="600"></canvas>
  <div class="stats">
    <p>Accel Max: <span id="accelMax">0.00</span> G</p>
    <p>Brake Max: <span id="brakeMax">0.00</span> G</p>
    <p>Lateral Max: <span id="lateralMax">0.00</span> G</p>
  </div>

  <script>
    const canvas = document.getElementById("gBall");
    const ctx = canvas.getContext("2d");
    const centerX = canvas.width / 2;
    const centerY = canvas.height / 2;
    const radius = 20;
    const sensitivity = 100;
    let xG = 0, yG = 0;
    let maxAccel = 0, maxBrake = 0, maxLateral = 0;

    const ws = new WebSocket("wss://" + location.host + "/ws");

    ws.onmessage = function(event) {
      const data = JSON.parse(event.data);
      xG = data.xG;
      yG = data.yG;

      if (xG > 0 && xG > maxAccel) maxAccel = xG;
      if (xG < 0 && Math.abs(xG) > maxBrake) maxBrake = Math.abs(xG);
      if (Math.abs(yG) > maxLateral) maxLateral = Math.abs(yG);

      document.getElementById("accelMax").textContent = maxAccel.toFixed(2);
      document.getElementById("brakeMax").textContent = maxBrake.toFixed(2);
      document.getElementById("lateralMax").textContent = maxLateral.toFixed(2);
    };

    function draw() {
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      const xBall = centerX + yG * sensitivity;
      const yBall = centerY - xG * sensitivity;

      ctx.beginPath();
      ctx.arc(centerX, centerY, 200, 0, 2 * Math.PI);
      ctx.strokeStyle = "#999";
      ctx.stroke();

      ctx.beginPath();
      ctx.arc(xBall, yBall, radius, 0, 2 * Math.PI);
      ctx.fillStyle = (xG > 0.15) ? "red" : "lime";
      ctx.fill();

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
                latest_data.update(eval(data))
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
