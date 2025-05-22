from dronekit import connect, VehicleMode, LocationGlobalRelative
import time
import math

# Підключення до дрона
print("Connecting to vehicle on: tcp:127.0.0.1:5762")
vehicle = connect('tcp:127.0.0.1:5762', wait_ready=True)

# Функція: взліт до заданої висоти
def arm_and_takeoff(target_altitude):
    while not vehicle.is_armable:
        print("Очікування готовності дрона до запуску...")
        time.sleep(1)

    vehicle.mode = VehicleMode("GUIDED")
    while vehicle.mode.name != "GUIDED":
        print("Очікування встановлення режиму GUIDED...")
        time.sleep(1)

    vehicle.armed = True
    while not vehicle.armed:
        print("Очікування активації дрона (arming)...")
        time.sleep(1)

    print("Зліт на висоту %d метрів" % target_altitude)
    vehicle.simple_takeoff(target_altitude)

    while True:
        altitude = vehicle.location.global_relative_frame.alt
        print(f"Поточна висота: {altitude:.1f} м")
        if altitude >= target_altitude * 0.95:
            print("Досягнута цільова висота")
            break
        time.sleep(1)

# Функція: обертання на азимут (yaw)
def set_yaw(heading, relative=False):
    is_relative = 1 if relative else 0
    msg = vehicle.message_factory.command_long_encode(
        0, 0,
        115, 0,        # MAV_CMD_CONDITION_YAW
        heading,       # yaw в градусах
        0,             # yaw speed
        1,             # direction (-1: CCW, 1: CW)
        is_relative,   # відносно чи абсолютно
        0, 0, 0        # непотрібні параметри
    )
    vehicle.send_mavlink(msg)

# Початкові координати (точка A = дім)
home_location = LocationGlobalRelative(50.450739, 30.461242, 100)

# Точка B
target_location = LocationGlobalRelative(50.443326, 30.448078, 100)

# Основна послідовність дій
arm_and_takeoff(100)

print("Летимо до точки B...")
vehicle.simple_goto(target_location)

# Чекаємо прибуття (можна точніше обчислювати за відстанню)
time.sleep(150)

print("Обертання на азимут 350 градусів...")
set_yaw(350)

time.sleep(5)
# Повторно надіслати команду goto на те саме місце (утримання позиції)
vehicle.simple_goto(target_location)

print("Сценарій завершено. Залишаємо дрон у повітрі.")
