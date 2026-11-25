import time
import random
import paho.mqtt.client as mqtt

# ================= KONFIGURASI MQTT =================
BROKER = "localhost"  # Sesuaikan dengan broker Node-RED (misal "localhost")
PORT = 1883

# Ganti NIM_ANDA dengan NIM Anda yang sebenarnya
NIM = "2410010260"
TOPIC_SUHU = f"iot/{NIM}/sensor/suhu"
TOPIC_RELAY = f"iot/{NIM}/aktuator/relay"
TOPIC_PWM = f"iot/{NIM}/aktuator/pwm"

# Opsional: Dukungan GPIO jika dijalankan di Raspberry Pi (otomatis fallback ke mode simulasi di PC)
try:
    import RPi.GPIO as GPIO
    HAS_GPIO = True
    RELAY_PIN = 26
    LED_PIN = 2
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(RELAY_PIN, GPIO.OUT)
    GPIO.setup(LED_PIN, GPIO.OUT)
    pwm_led = GPIO.PWM(LED_PIN, 1000)
    pwm_led.start(0)
except ImportError:
    HAS_GPIO = False
    print("[INFO] Library RPi.GPIO tidak ditemukan. Berjalan dalam mode simulasi perangkat PC.")

def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print("Terhubung ke MQTT Broker!")
        client.subscribe(TOPIC_RELAY)
        client.subscribe(TOPIC_PWM)
    else:
        print(f"Gagal terhubung, kode error: {rc}")

def on_message(client, userdata, msg):
    topic = msg.topic
    payload = msg.payload.decode("utf-8").strip()

    if topic == TOPIC_RELAY:
        if payload == "ON":
            if HAS_GPIO:
                GPIO.output(RELAY_PIN, GPIO.HIGH)
            print("[AKTUATOR] Relay GPIO 26 -> ON")
        elif payload == "OFF":
            if HAS_GPIO:
                GPIO.output(RELAY_PIN, GPIO.LOW)
            print("[AKTUATOR] Relay GPIO 26 -> OFF")

    elif topic == TOPIC_PWM:
        try:
            pwm_val = max(0, min(255, int(float(payload))))
            if HAS_GPIO:
                duty_cycle = (pwm_val / 255.0) * 100.0
                pwm_led.ChangeDutyCycle(duty_cycle)
            print(f"[AKTUATOR] LED PWM GPIO 2 -> {pwm_val}/255")
        except ValueError:
            print(f"[ERROR] Nilai PWM tidak valid: {payload}")

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.on_connect = on_connect
client.on_message = on_message

client.connect(BROKER, PORT, 60)
client.loop_start()

try:
    while True:
        # Membaca suhu (gunakan library Adafruit_DHT jika pakai sensor fisik, atau simulasi realistis)
        suhu = round(random.uniform(26.0, 33.5), 2)
        client.publish(TOPIC_SUHU, str(suhu))
        print(f"[SENSOR] Mengirim suhu ke {TOPIC_SUHU}: {suhu} °C")
        time.sleep(3)  # Kirim setiap 3 detik

except KeyboardInterrupt:
    print("\nProgram dihentikan.")
    client.loop_stop()
    client.disconnect()
    if HAS_GPIO:
        pwm_led.stop()
        GPIO.cleanup()
