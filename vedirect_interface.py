import time
import serial

ser = serial.Serial(
port='/dev/ttyUSB0',
baudrate = 19200,
parity=serial.PARITY_NONE,
stopbits=serial.STOPBITS_ONE,
bytesize=serial.EIGHTBITS,
timeout=1
)

or = {
0x001: 'No input power',
0x002: 'Switched off (power switch)',
0x004: 'Switched off (register)',
0x008: 'Remote input',
0x010: 'Protection active',
0x020: 'Paygo',
0x040: 'BMS',
0x080: 'Engine shutdown detection',
0x100: 'Analysing input voltage'
}

cs = {
0: 'Not charging',
2: 'Fault',
3: 'Bulk',
4: 'Absorption',
5: 'Float',
7: 'Equalize (manual)',
245: 'Starting-up',
247: 'Auto equalize',
252: 'External control'
}

err = {
0: 'No error',
2: 'Battery voltage too high',
3: 'Remote temperature sensor failure',
4: 'Remote temperature sensor failure',
5: 'Remote temperature sensor failure (connection lost)',
6: 'Remote battery voltage sense failure',
7: 'Remote battery voltage sense failure',
8: 'Remote battery voltage sense failure (connection lost)',
17: 'Charger temperature too high',
18: 'Charger over current',
19: 'Charger current reversed',
20: 'Bulk time limit exceeded',
21: 'Current sensor issue (sensor bias/sensor broken)',
26: 'Terminals overheated',
28: 'Power stage issue',
33: 'Input voltage too high (solar panel)',
34: 'Input current too high (solar panel)',
38: 'Input shutdown (due to excessive battery voltage)',
39: 'Input shutdown',
65: 'Lost communication',
66: 'Charging configuartion issue',
67: 'BMS Connection lost',
68: 'Network misconfigured'
114: 'CPU temperature too high',
116: 'Factory calibration data lost',
117: 'Invalid/incompatible firmware',
119: 'User settings invalid'
}

mppt = {
0: 'Off',
1: 'Voltage or current limited',
2: 'MPP Tracker active'
}
