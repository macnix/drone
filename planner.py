from dronekit import connect, VehicleMode
import time

# === RC Override значення ===
ALT_HOLD_THROTTLE_ASCENT = 1990    # Канал 3 — throttle для підйому (вище 1500)
ALT_HOLD_THROTTLE_HOVER = 1500     # Канал 3 — throttle для зависання (точно 1500)
FORWARD_PITCH = 1550               # Канал 2 — pitch вперед
YAW_RIGHT = 1600                   # Канал 4 — yaw вправо
NEUTRAL = 1500                     # Центрування каналів

TARGET_TAKEOFF_ALT_M = 5           # Мінімальна висота для стабільного зльоту
ASCENT_DURATION_SEC = 5            # Тривалість подачі throttle для початкового підйому

# === Підключення до SITL ===
print("🔌 Підключення до дрона (TCP 5762)...")
try:
    vehicle = connect('tcp:127.0.0.1:5762', wait_ready=True, timeout=60)
except Exception as e:
    print(f"❌ Не вдалося підключитися до дрона: {e}")
    exit()

def wait_for_mode(mode_name):
    """Очікуємо активації режиму"""
    print(f"🎛 Встановлюємо режим {mode_name}...")
    vehicle.mode = VehicleMode(mode_name)
    while vehicle.mode.name != mode_name:
        print(f"⏳ Очікуємо {mode_name}...")
        time.sleep(0.5)
    print(f"✅ Режим {mode_name} активовано")

def wait_for_arm():
    """Очікуємо ARM дрона"""
    print("🛠 ARM дрона...")
    vehicle.armed = True
    while not vehicle.armed:
        print("🔄 Очікуємо ARM...")
        time.sleep(0.5)
    print("✅ Дрон ARMовано")

def wait_for_disarm():
    """Очікуємо DISARM дрона"""
    print("🛑 DISARM дрона...")
    vehicle.armed = False
    while vehicle.armed:
        print("🔻 Очікуємо DISARM...")
        time.sleep(0.5)
    print("✅ Дрон DISARMовано")

# === Очікування GPS ===
print("📡 Очікуємо фіксацію GPS...")
# Додаткова перевірка, що дрон не ARM'лений під час очікування GPS (хоча DroneKit це зазвичай не дозволяє)
# Або можна додати невеличку затримку після отримання GPS, щоб дрон "оселився"
while vehicle.gps_0.fix_type < 3:
    print(f"⏳ GPS fix type: {vehicle.gps_0.fix_type} | Супутники: {vehicle.gps_0.satellites_visible}")
    time.sleep(1)
print("✅ GPS фіксація OK")
time.sleep(2) # Додаткова затримка після GPS fix для стабілізації

try:
    # === Встановлюємо ALT_HOLD ===
    wait_for_mode("ALT_HOLD")

    # === ARM ===
    wait_for_arm()

    # === Зліт за допомогою throttle override ===
    print(f"🛫 Зліт. Подача throttle {ALT_HOLD_THROTTLE_ASCENT} протягом {ASCENT_DURATION_SEC} секунд...")
    vehicle.channels.overrides = {'3': ALT_HOLD_THROTTLE_ASCENT}
    time.sleep(ASCENT_DURATION_SEC) # Тримаємо throttle на підйом протягом фіксованого часу

    print(f"✅ Початковий підйом виконано. Перевіряємо висоту до {TARGET_TAKEOFF_ALT_M} м...")

    # Перемикаємо на режим зависання
    vehicle.channels.overrides['3'] = ALT_HOLD_THROTTLE_HOVER

    # Моніторинг висоти до досягнення цільової висоти
    while True:
        alt = vehicle.location.global_relative_frame.alt
        print(f"🔼 Поточна висота: {alt:.2f} м (цільова: {TARGET_TAKEOFF_ALT_M} м)")
        if alt >= TARGET_TAKEOFF_ALT_M:
            print(f"✅ Досягнуто висоти {alt:.2f} м, що більше або дорівнює {TARGET_TAKEOFF_ALT_M} м.")
            break
        time.sleep(0.5)

    print("✅ Дрон стабільно зависає.")

    # === Рух вперед (Pitch вперед) ===
    print("➡️ Політ вперед (20 секунд)...")
    vehicle.channels.overrides['2'] = FORWARD_PITCH
    start_time = time.time()
    while time.time() - start_time < 20:  # 20 секунд
        print(f"📍 Координати: Lat={vehicle.location.global_frame.lat:.6f}, Lon={vehicle.location.global_frame.lon:.6f} | Висота: {vehicle.location.global_relative_frame.alt:.2f} м")
        time.sleep(1)

    # === Поворот (Yaw) ===
    print("↪️ Поворот праворуч (Yaw, 3 секунди)...")
    vehicle.channels.overrides['2'] = NEUTRAL  # Зупиняємо рух вперед
    vehicle.channels.overrides['4'] = YAW_RIGHT
    time.sleep(3)
    vehicle.channels.overrides['4'] = NEUTRAL

    # === Завершення ===
    print("🛑 Завершення маневрів. Нейтралізація каналів.")
    vehicle.channels.overrides = {} # Скидаємо всі override

except KeyboardInterrupt:
    print("\n🚨 Виявлено Ctrl+C! Переходимо в режим LAND...")
    vehicle.channels.overrides = {} # Скидаємо всі override
    wait_for_mode("LAND") # Переводимо дрон в режим посадки

finally:
    # DISARM
    wait_for_disarm()

    # Закриття з'єднання
    vehicle.close()
    print("✅ Місія завершена. З'єднання закрито.")
