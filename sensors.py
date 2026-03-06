import time
import board
import busio

import adafruit_bme280

from adafruit_bno08x import (
    BNO_REPORT_ACCELEROMETER,
    BNO_REPORT_GYROSCOPE,
    BNO_REPORT_ROTATION_VECTOR
)

from adafruit_bno08x.i2c import BNO08X_I2C


def init_i2c():
    return busio.I2C(board.SCL, board.SDA, frequency=400000)


def init_bme280(i2c):
    bme280 = adafruit_bme280.Adafruit_BME280_I2C(i2c, address=0x76)
    bme280.sea_level_pressure = 1013.25
    return bme280


def init_bno085(i2c):
    bno = BNO08X_I2C(i2c)

    bno.enable_feature(BNO_REPORT_ACCELEROMETER)
    bno.enable_feature(BNO_REPORT_GYROSCOPE)
    bno.enable_feature(BNO_REPORT_ROTATION_VECTOR)

    return bno


def main():

    print("Initializing I2C...")
    i2c = init_i2c()

    print("Initializing BME280...")
    bme280 = init_bme280(i2c)

    print("Initializing BNO085...")
    bno = init_bno085(i2c)

    print("Sensors ready\n")

    while True:

        try:

            # ----- BME280 -----

            temperature = bme280.temperature
            humidity = bme280.relative_humidity
            pressure = bme280.pressure
            altitude = bme280.altitude

            # ----- BNO085 -----

            accel_x, accel_y, accel_z = bno.acceleration
            gyro_x, gyro_y, gyro_z = bno.gyro
            quat_i, quat_j, quat_k, quat_real = bno.quaternion

            print("====== WEATHER DATA ======")
            print(f"Temp: {temperature:.2f} C")
            print(f"Humidity: {humidity:.2f} %")
            print(f"Pressure: {pressure:.2f} hPa")
            print(f"Altitude: {altitude:.2f} m")

            print("\n====== IMU DATA ======")
            print(f"Accel (m/s^2): {accel_x:.3f}, {accel_y:.3f}, {accel_z:.3f}")
            print(f"Gyro (rad/s): {gyro_x:.3f}, {gyro_y:.3f}, {gyro_z:.3f}")
            print(f"Quaternion: {quat_i:.3f}, {quat_j:.3f}, {quat_k:.3f}, {quat_real:.3f}")

            print("\n-----------------------------\n")

            time.sleep(2)

        except Exception as e:
            print("Error:", e)
            time.sleep(2)


if __name__ == "__main__":
    main()