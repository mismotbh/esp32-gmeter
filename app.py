
from flask import Flask, render_template_string, request
from flask_socketio import SocketIO, emit
import time

app = Flask(__name__)
socketio = SocketIO(app, async_mode='eventlet')

# Variables to store max values
max_lat = 0.0
max_acc = 0.0
max_dec = 0.0

# For smoothing peak detection
last_update_time = time.time()
buffer = []

@app.route('/')
def index():
    return render_template_string("""
<!DOCTYPE html>
<html>
<head>
    <title>Night Owl Racing - G Meter</title>
    <style>
        body {
            margin: 0;
            font-family: Arial, sans-serif;
            background-color: black;
            color: yellow;
            text-align: center;
        }
        #g-meter {
            width: 300px;
            height: 300px;
            margin: 20px auto;
            border: 4px solid yellow;
            border-radius: 50%;
            position: relative;
            background: radial-gradient(black 30%, #222 100%);
        }
        #dot {
            width: 20px;
            height: 20px;
            background-color: red;
            border-radius: 50%;
            position: absolute;
            top: 140px;
            left: 140px;
            transition: top 0.05s, left 0.05s;
        }
        .metrics {
            font-size: 24px;
            margin: 10px 0;
        }
        .title {
            font-size: 32px;
            font-weight: bold;
            margin-top: 10px;
            color: yellow;
        }
        .label {
            font-size: 20px;
            color: white;
        }
        .value {
            font-size: 30px;
            font-weight: bold;
        }
    </style>
</head>
<body>
    <div class="title">G-FORCE METER</div>
    <div id="g-meter"><div id="dot"></div></div>
    <div class="metrics">
        <span class="label">Live G:</span> <span class="value" id="liveG">0.00</span> G
    </div>
    <div class="metrics">
        <span class="label">PEAK LAT:</span> <span class="value" id="peakLat">+0.00</span> G
    </div>
    <div class="metrics">
        <span class="label">PEAK ACC:</span> <span class="value" id="peakAcc">+0.00</span> G
    </div>
    <div class="metrics">
        <span class="label">PEAK DEC:</span> <span class="value" id="peakDec">-0.00</span> G
    </div>

<script src="https://cdn.socket.io/4.3.2/socket.io.min.js"></script>
<script>
    const socket = io();

    socket.on('gforce', data => {
        const { xG, yG, maxLat, maxAcc, maxDec } = data;

        const scale = 100;
        const center = 150;
        const x = center + xG * scale;
        const y = center - yG * scale;

        const dot = document.getElementById("dot");
        dot.style.left = `${x - 10}px`;
        dot.style.top = `${y - 10}px`;

        document.getElementById("liveG").innerText = (Math.sqrt(xG * xG + yG * yG)).toFixed(2);
        document.getElementById("peakLat").innerText = (maxLat).toFixed(2);
        document.getElementById("peakAcc").innerText = (maxAcc).toFixed(2);
        document.getElementById("peakDec").innerText = (-maxDec).toFixed(2);
    });
</script>
</body>
</html>
""")

@socketio.on('update_gforce')
def handle_gforce(data):
    global max_lat, max_acc, max_dec, buffer, last_update_time

    xG = float(data['xG'])
    yG = float(data['yG'])

    buffer.append((time.time(), xG, yG))
    buffer = [entry for entry in buffer if time.time() - entry[0] <= 0.25]

    avg_x = sum(x for _, x, _ in buffer) / len(buffer)
    avg_y = sum(y for _, _, y in buffer) / len(buffer)

    lat = abs(avg_x)
    acc = max(0, -avg_y)
    dec = max(0, avg_y)

    if lat > max_lat:
        max_lat = lat
    if acc > max_acc:
        max_acc = acc
    if dec > max_dec:
        max_dec = dec

    socketio.emit('gforce', {
        'xG': xG,
        'yG': yG,
        'maxLat': max_lat,
        'maxAcc': max_acc,
        'maxDec': max_dec
    })

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)
