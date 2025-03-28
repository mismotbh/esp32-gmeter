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
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@600&display=swap');

    * { box-sizing: border-box; }

    body {
      margin: 0;
      background-color: #000;
      color: #FFD700;
      font-family: 'Orbitron', sans-serif;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: flex-start;
      height: 100vh;
      overflow: hidden;
    }

    .branding {
      margin-top: 10px;
      font-size: 4vw;
      color: #FFD700;
      text-shadow: 0 0 10px #FFD700;
      letter-spacing: 2px;
    }

    .container {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      flex: 1;
      width: 100%;
    }

    canvas {
      width: 80vw;
      height: 80vw;
      max-width: 500px;
      max-height: 500px;
      background: radial-gradient(circle at center, #111 60%, #000);
      border: 3px solid #FFD700;
      border-radius: 20px;
      box-shadow: 0 0 30px #FFD70033;
    }

    .dashboard {
      margin-top: 20px;
      background: #111;
      border: 2px solid #FFD700;
      border-radius: 12px;
      padding: 15px 25px;
      text-align: center;
      box-shadow: 0 0 20px #FFD70022;
      width: 90vw;
      max-width: 360px;
    }

    .dashboard p {
      margin: 10px 0;
      font-size: 4vw;
      color: #ffeb7a;
    }

    .highlight, #xG, #yG {
      color: #fff689;
      font-weight: bold;
      display: inline-block;
      min-width: 3.6em;
      font-family: 'Courier New', monospace;
      text-align: right;
    }

    .live {
      font-size: 4.5vw;
      color: #FFD700;
      margin-top: 10px;
      text-align: center;
    }
  </style>
</head>
<body>
  <div class="branding">🏁 Night Owl Racing</div>

  <div class="container">
    <canvas id="gBall"></canvas>

    <div class="dashboard">
      <div class="live">
        xG: <span id="xG">0.00</span> | yG: <span id="yG">0.00</span>
      </div>
      <p>Brake Max: <span class="highlight" id="brakeMax">0.00</span> G</p>
      <p>Accel Max: <span class="highlight" id="accelMax">0.00</span> G</p>
      <p>Lateral Max: <span class="highlight" id="lateralMax">0.00</span> G</p>
    </div>
  </div>

  <script>
    const canvas = document.getElementById("gBall");
    const ctx = canvas.getContext("2d");

    function resizeCanvas() {
      canvas.width = canvas.clientWidth;
      canvas.height = canvas.clientHeight;
    }
    window.addEventListener('resize', resizeCanvas);
    resizeCanvas();

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
      const width = canvas.width;
      const height = canvas.height;
      const centerX = width / 2;
      const centerY = height / 2;
      const radius = width * 0.04;
      const outerR = width * 0.4;
      const sensitivity = outerR / 2;

      ctx.clearRect(0, 0, width, height);

      const xBall = centerX + yG * sensitivity;
      const yBall = centerY - xG * sensitivity;

      // Outer circle
      ctx.beginPath();
      ctx.arc(centerX, centerY, outerR, 0, 2 * Math.PI);
      ctx.strokeStyle = "#FFD700";
      ctx.lineWidth = 3;
      ctx.stroke();

      // Crosshair
      ctx.strokeStyle = "#FFD70044";
      ctx.lineWidth = 1.5;
      ctx.beginPath();
      ctx.moveTo(centerX - outerR, centerY);
      ctx.lineTo(centerX + outerR, centerY);
      ctx.stroke();
      ctx.beginPath();
      ctx.moveTo(centerX, centerY - outerR);
      ctx.lineTo(centerX, centerY + outerR);
      ctx.stroke();

      // Ball gradient
      const gradient = ctx.createRadialGradient(xBall, yBall, 5, xBall, yBall, radius);
      gradient.addColorStop(0, "#fff");
      gradient.addColorStop(0.4, (xG > 0.15) ? "#ff3333" : "#66ff66");
      gradient.addColorStop(1, "#111");

      ctx.beginPath();
      ctx.arc(xBall, yBall, radius, 0, 2 * Math.PI);
      ctx.fillStyle = gradient;
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
