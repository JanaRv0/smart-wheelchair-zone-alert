from flask import Flask, request, jsonify, render_template
import pyodbc
import smtplib

app = Flask(__name__)

# Azure SQL connection string
conn_str = (
    "Driver={ODBC Driver 17 for SQL Server};"
    "Server=tcp:iotwheel.database.windows.net,1433;"
    "Database=ZoneDB;"
    "Uid=jananan;"
    "Pwd=Ravi@1965;"
    "Encrypt=yes;"
    "TrustServerCertificate=no;"
    "Connection Timeout=30;"
)

# Email alert function
def send_email(to_email, subject, body):
    sender = "csleaner1122@gmail.com"
    password = "MMMM12344321"
    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(sender, password)
    message = f"Subject: {subject}\n\n{body}"
    server.sendmail(sender, to_email, message)
    server.quit()

# ✅ API: Receive zone alert from ESP32
@app.route('/api/zonealert', methods=['POST'])
def zone_alert():
    data = request.json
    bssid = data.get("bssid")
    wheelchair_id = data.get("wheelchair_id")

    try:
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        cursor.execute("SELECT zone_name, staff_email FROM ZoneMap WHERE mac_address = ?", bssid)
        row = cursor.fetchone()

        if row:
            zone, email = row
            cursor.execute("SELECT zone_name FROM StudentMap WHERE student_id = ?", wheelchair_id)
            current_zone_row = cursor.fetchone()
            current_zone = current_zone_row[0] if current_zone_row else None

            if current_zone != zone:
                cursor.execute("UPDATE StudentMap SET zone_name = ? WHERE student_id = ?", zone, wheelchair_id)
                conn.commit()
                send_email(email, f"Wheelchair {wheelchair_id} entered {zone}", f"Alert: Wheelchair {wheelchair_id} has entered {zone}.")
                return jsonify({"status": "alert sent", "zone": zone}), 200
            else:
                return jsonify({"status": "no change", "zone": zone}), 200
        else:
            return jsonify({"error": "BSSID not found"}), 404

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ✅ API: Get current location of a wheelchair
@app.route('/api/location/<wheelchair_id>', methods=['GET'])
def get_location(wheelchair_id):
    try:
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        cursor.execute("SELECT zone_name FROM StudentMap WHERE student_id = ?", wheelchair_id)
        row = cursor.fetchone()

        if row:
            return jsonify({"wheelchair_id": wheelchair_id, "zone": row[0]}), 200
        else:
            return jsonify({"error": "Wheelchair not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ✅ UI: Location viewer page
@app.route('/location/<wheelchair_id>')
def location_page(wheelchair_id):
    return render_template('location.html', wheelchair_id=wheelchair_id)

# ✅ UI: Home page or dashboard
@app.route('/')
def home():
    return render_template('dashboard.html')

if __name__ == '__main__':
    app.run(debug=True)
@app.route('/api/locations', methods=['GET'])
def get_all_locations():
    cursor = conn.cursor()
    cursor.execute("SELECT student_id, zone_name FROM StudentMap")
    rows = cursor.fetchall()
    return jsonify([{"wheelchair_id": r[0], "zone": r[1]} for r in rows])
