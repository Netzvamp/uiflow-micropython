# SPDX-FileCopyrightText: 2024 M5Stack Technology CO LTD
#
# SPDX-License-Identifier: MIT

_attrs = {
    "ACMeasureUnit": "ac_measure",
    "AccelUnit": "accel",
    "ADCV11Unit": "adc_v11",
    "ADCUnit": "adc",
    "AIN4_20MAUnit": "ain4_20ma",
    "AMeterUnit": "ameter",
    "AngleUnit": "angle",
    "Angle8Unit": "angle8",
    "BLDCDriverUnit": "bldc_driver",
    "BPSUnit": "bps",
    "ButtonUnit": "button",
    "BuzzerUnit": "buzzer",
    "CardKBUnit": "cardkb",
    "CANUnit": "can",
    "MiniCANUnit": "can",
    "KeyCode": "cardkb",
    "CatchUnit": "catch",
    "CATMGNSSUnit": "catm_gnss",
    "CATMUnit": "catm",
    "CO2Unit": "co2",
    "CO2LUnit": "co2l",
    "ColorUnit": "color",
    "DACUnit": "dac",
    "DAC2Unit": "dac2",
    "DDSUnit": "dds",
    "DigiClockUnit": "digi_clock",
    "DLightUnit": "dlight",
    "DMX512Unit": "dmx",
    "DualButtonUnit": "dual_button",
    "EarthUnit": "earth",
    "EncoderUnit": "encoder",
    "Encoder8Unit": "encoder8",
    "ENVUnit": "env",
    "ENVPROUnit": "envpro",
    "ExtEncoderUnit": "extencoder",
    "EXTIOUnit": "extio",
    "EXTIO2Unit": "extio2",
    "FaderUnit": "fader",
    "FanUnit": "fan",
    "FingerUnit": "finger",
    "FlashLightUnit": "flash_light",
    "GestureUnit": "gesture",
    "GlassUnit": "glass",
    "Glass2Unit": "glass2",
    "GPSUnit": "gps",
    "Grove2GroveUnit": "grove2grove",
    "HallEffectUnit": "hall_effect",
    "HbridgeUnit": "hbridge",
    "HeartUnit": "heart",
    "IMUProUnit": "imu_pro",
    "IMUUnit": "imu",
    "IRUnit": "ir",
    "JoystickUnit": "joystick",
    "KeyUnit": "key",
    "KMeterISOUnit": "kmeter_iso",
    "KMeterUnit": "kmeter",
    "LaserRXUnit": "laser_rx",
    "LaserTXUnit": "laser_tx",
    "LCDUnit": "lcd",
    "LightUnit": "light",
    "LIMITUnit": "limit",
    "LoRaE220433Unit": "lora_e220_433",
    "LoRaE220JPUnit": "lora_e220_jp",
    "LoRaWANUnit": "lorawan",
    "MIDIUnit": "midi",
    "MiniOLEDUnit": "minioled",
    "MiniScaleUnit": "miniscale",
    "MQTTUnit": "mqtt",
    "MQTTPoEUnit": "mqttpoe",
    "NBIOTUnit": "nbiot",
    "NCIRUnit": "ncir",
    "NCIR2Unit": "ncir2",
    "NECOUnit": "neco",
    "OLEDUnit": "oled",
    "OPUnit": "op",
    "PAHUBUnit": "pahub",
    "PBHUBUnit": "pbhub",
    "PIRUnit": "pir",
    "QRCodeUnit": "qrcode",
    "RCAUnit": "rca",
    "ReflectiveIRUnit": "reflective_ir",
    "RelayUnit": "relay",
    "Relay4Unit": "relay4",
    "Relay2Unit": "relay2",
    "RFIDUnit": "rfid",
    "RGBUnit": "rgb",
    "ISO485Unit": "rs485_iso",
    "RS485Unit": "rs485",
    "RTC8563Unit": "rtc8563",
    "ScalesUnit": "scales",
    "ScrollUnit": "scroll",
    "Servos8Unit": "servos8",
    "SSRUnit": "ssr",
    "SynthUnit": "synth",
    "ThermalUnit": "thermal",
    "Thermal2Unit": "thermal2",
    "TMOSUnit": "tmos",
    "ToFUnit": "tof",
    "TOF4MUnit": "tof4m",
    "TubePressureUnit": "tube_pressure",
    "TVOCUnit": "tvoc",
    "UltrasoundI2CUnit": "ultrasonic_i2c",
    "UltrasoundIOUnit": "ultrasonic_io",
    "VibratorUnit": "vibrator",
    "UWBUnit": "uwb",
    "VoltmeterUnit": "vmeter",
    "WateringUnit": "watering",
    "WeightI2CUnit": "weight_i2c",
    "WeightUnit": "weight",
    "ZigbeeUnit": "zigbee",
}


def __getattr__(attr):
    mod = _attrs.get(attr, None)
    if mod is None:
        raise AttributeError(attr)
    value = getattr(__import__(mod, None, None, True, 1), attr)
    globals()[attr] = value
    return value
