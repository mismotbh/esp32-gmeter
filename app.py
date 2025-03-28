from flask import Flask, render_template_string
from flask_sock import Sock

app = Flask(__name__)
sock = Sock(app)
clients = set()

HTML = """
<!DOCTYPE html>
<html>
<head>
  <title>Night Owl Racing - G Meter</title>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@600&display=swap');

    body {
      margin: 0;
      background-color: #0a0a0a;
      color: #FFD700;
      font-family: 'Orbitron', sans-serif;
      display: flex;
      flex-direction: column;
      align-items: center;
    }

    .branding {
      position: absolute;
      top: 20px;
      left: 30px;
      font-size: 28px;
      color: #FFD700;
      text-shadow: 0 0 10px #FFD700;
      letter-spacing: 2px;
    }

    canvas {
      margin-top: 100px;
      background: radial-gradient(circle, #111 60%, #000);
      border: 3px solid #FFD700;
      border-radius: 10px;
      box-shadow: 0 0 25px #FFD70044;
    }

    .live {
      font-size: 1.6em;
      color: #FFD700;
      margin: 30px 0 10px 0;
    }

    .dashboard {
      background: #111;
      border: 2px solid #FFD700;
      border-radius: 8px;
      padding: 20px 30px;
      margin-bottom: 50px;
      width: 300px;
      box-shadow: 0 0 15px #FFD70033;
    }

    .dashboard p {
      margin: 10px 0;
      font-size: 1.2em;
      color: #ffeb7a;
    }

    .highlight {
      color: #fff689;
      font-weight: bold;
    }
  </style>
</head>
<body>
  <div class="branding">🏁 Night Owl Racing</div>

  <canvas id="gBall" width="600" height="600"></canvas>

  <div class="live">
    xG: <span id="xG">0.00</span> | yG: <span id="yG">0.00</span>
  </div>

  <div class="dashboard">
    <p>Brake Max: <span class="highlight" id="brakeMax">0.00</span> G</p>
    <p>Accel Max: <span class="highlight" id="accelMax">0.00</span> G</p>
    <p>Lateral Max: <span class="highlight" id="lateralMax">0.00</span> G</p>
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

    let candidateAccel = null, accelStart = 0;
    let candidateBrake = null, brakeStart = 0;
    let candidateLat = null, latStart = 0;

    const threshold = 0.3;
    const sustainTime = 250;
    const matchRange = 0.1;

    const ws = new WebSocket("wss://" + location.host + "/ws");

    ws.onmessage = function(event) {
      const data = JSON.parse(event.data);
      xG = data.xG;
      yG = data.yG;

      document.getElementById("xG").textContent = xG.toFixed(2);
      document.getElementById("yG").textContent = yG.toFixed(2);

      const now = Date.now();

      // Braking (xG > 0)
      if (xG > threshold) {
        if (candidateBrake === null || Math.abs(xG - candidateBrake) > matchRange) {
          candidateBrake = xG;
          brakeStart = now;
        } else if (now - brakeStart >= sustainTime && xG > maxBrake) {
          maxBrake = xG;
          candidateBrake = null;
        }
      } else {
        candidateBrake = null;
      }

      // Acceleration (xG < 0)
      if (xG < -threshold) {
        const accelG = Math.abs(xG);
        if (candidateAccel === null || Math.abs(accelG - candidateAccel) > matchRange) {
          candidateAccel = accelG;
          accelStart = now;
        } else if (now - accelStart >= sustainTime && accelG > maxAccel) {
          maxAccel = accelG;
          candidateAccel = null;
        }
      } else {
        candidateAccel = null;
      }

      // Lateral
      const latG = Math.abs(yG);
      if (latG > threshold) {
        if (candidateLat === null || Math.abs(latG - candidateLat) > matchRange) {
          candidateLat = latG;
          latStart = now;
        } else if (now - latStart >= sustainTime && latG > maxLateral) {
          maxLateral = latG;
          candidateLat = null;
        }
      } else {
        candidateLat = null;
      }

      document.getElementById("brakeMax").textContent = maxBrake.toFixed(2);
      document.getElementById("accelMax").textContent = maxAccel.toFixed(2);
      document.getElementById("lateralMax").textContent = maxLateral.toFixed(2);
    };

    function draw() {
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      const xBall = centerX + yG * sensitivity;
      const yBall = centerY - xG * sensitivity;

      ctx.beginPath();
      ctx.arc(centerX, centerY, 200, 0, 2 * Math.PI);
      ctx.strokeStyle = "#FFD700";
      ctx.stroke();

      ctx.beginPath();
      ctx.arc(xBall, yBall, radius, 0, 2 * Math.PI);
      ctx.fillStyle = (xG > 0.15) ? "red" : "lime";  // Red = braking
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
