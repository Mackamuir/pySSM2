"""
ECU Capability Definitions for SSM2 Protocol

This module contains the mapping of ECU initialization response bytes to capability flags.
Based on ssm_info.txt documentation.

Each capability byte contains 8 bits representing different ECU features.
Bit 7 is MSB, Bit 0 is LSB.
"""

# Capability byte definitions
# Format: (byte_index, bit_position, category, name)
CAPABILITY_MAP = [
    # Byte 9 (index 0)
    (0, 7, 'sensors', 'Engine Load'),
    (0, 6, 'sensors', 'Coolant Temperature'),
    (0, 5, 'sensors', 'Air/Fuel Correction #1'),
    (0, 4, 'sensors', 'Air/Fuel Learning #1'),
    (0, 3, 'sensors', 'Air/Fuel Correction #2'),
    (0, 2, 'sensors', 'Air/Fuel Learning #2'),
    (0, 1, 'sensors', 'Manifold Absolute Pressure'),
    (0, 0, 'sensors', 'Engine Speed'),

    # Byte 10 (index 1)
    (1, 7, 'sensors', 'Vehicle Speed'),
    (1, 6, 'sensors', 'Ignition Timing'),
    (1, 5, 'sensors', 'Intake Air Temperature'),
    (1, 4, 'sensors', 'Mass Air Flow'),
    (1, 3, 'sensors', 'Throttle Opening Angle'),
    (1, 2, 'sensors', 'Front O2 Sensor #1'),
    (1, 1, 'sensors', 'Rear O2 Sensor'),
    (1, 0, 'sensors', 'Front O2 Sensor #2'),

    # Byte 11 (index 2)
    (2, 7, 'sensors', 'Battery Voltage'),
    (2, 6, 'sensors', 'Air Flow Sensor Voltage'),
    (2, 5, 'sensors', 'Throttle Sensor Voltage'),
    (2, 4, 'sensors', 'Differential Pressure Sensor Voltage'),
    (2, 3, 'sensors', 'Fuel Injection #1 Pulse Width'),
    (2, 2, 'sensors', 'Fuel Injection #2 Pulse Width'),
    (2, 1, 'sensors', 'Knock Correction'),
    (2, 0, 'sensors', 'Atmospheric Pressure'),

    # Byte 12 (index 3)
    (3, 7, 'sensors', 'Manifold Relative Pressure'),
    (3, 6, 'sensors', 'Pressure Differential Sensor'),
    (3, 5, 'sensors', 'Fuel Tank Pressure'),
    (3, 4, 'sensors', 'CO Adjustment'),
    (3, 3, 'sensors', 'Learned Ignition Timing'),
    (3, 2, 'sensors', 'Accelerator Opening Angle'),
    (3, 1, 'sensors', 'Fuel Temperature'),
    (3, 0, 'outputs', 'Front O2 Heater #1'),

    # Byte 13 (index 4)
    (4, 7, 'outputs', 'Rear O2 Heater Current'),
    (4, 6, 'outputs', 'Front O2 Heater #2'),
    (4, 5, 'sensors', 'Fuel Level'),
    (4, 3, 'outputs', 'Primary Wastegate Duty Cycle'),
    (4, 2, 'outputs', 'Secondary Wastegate Duty Cycle'),
    (4, 1, 'outputs', 'CPC Valve Duty Ratio'),
    (4, 0, 'sensors', 'Tumble Valve Position Sensor Right'),

    # Byte 14 (index 5)
    (5, 7, 'sensors', 'Tumble Valve Position Sensor Left'),
    (5, 6, 'outputs', 'Idle Speed Control Valve Duty Ratio'),
    (5, 5, 'sensors', 'Air/Fuel Lean Correction'),
    (5, 4, 'outputs', 'Air/Fuel Heater Duty'),
    (5, 3, 'outputs', 'Idle Speed Control Valve Step'),
    (5, 2, 'outputs', 'Number of Ex. Gas Recirc Steps'),
    (5, 1, 'outputs', 'Alternator Duty'),
    (5, 0, 'outputs', 'Fuel Pump Duty'),

    # Byte 15 (index 6)
    (6, 7, 'sensors', 'VVT Advance Angle Right'),
    (6, 6, 'sensors', 'VVT Advance Angle Left'),
    (6, 5, 'outputs', 'OCV Duty Right'),
    (6, 4, 'outputs', 'OCV Duty Left'),
    (6, 3, 'sensors', 'OCV Current Right'),
    (6, 2, 'sensors', 'OCV Current Left'),
    (6, 1, 'sensors', 'Air/Fuel Sensor #1 Current'),
    (6, 0, 'sensors', 'Air/Fuel Sensor #2 Current'),

    # Byte 16 (index 7)
    (7, 7, 'sensors', 'Air/Fuel Sensor #1 Resistance'),
    (7, 6, 'sensors', 'Air/Fuel Sensor #2 Resistance'),
    (7, 5, 'sensors', 'Air/Fuel Sensor #1'),
    (7, 4, 'sensors', 'Air/Fuel Sensor #2'),
    (7, 3, 'sensors', 'Air/Fuel Correction #3'),
    (7, 2, 'sensors', 'Air/Fuel Learning #3'),
    (7, 1, 'sensors', 'Rear O2 Heater Voltage'),
    (7, 0, 'sensors', 'Air/Fuel Adjustment Voltage'),

    # Byte 17 (index 8)
    (8, 5, 'sensors', 'Gear Position'),

    # Byte 18 (index 9)
    (9, 4, 'sensors', 'Air/Fuel Sensor #1 Heater Current'),
    (9, 3, 'sensors', 'Air/Fuel Sensor #2 Heater Current'),

    # Byte 20 (index 11)
    (11, 6, 'switches', 'AT Vehicle ID'),
    (11, 5, 'switches', 'Test Mode Connector'),
    (11, 4, 'switches', 'Read Memory Connector'),

    # Byte 21 (index 12)
    (12, 7, 'switches', 'Neutral Position Switch'),
    (12, 6, 'switches', 'Idle Switch'),
    (12, 4, 'switches', 'Intercooler AutoWash Switch'),
    (12, 3, 'switches', 'Ignition Switch'),
    (12, 2, 'switches', 'Power Steering Switch'),
    (12, 1, 'switches', 'Air Conditioning Switch'),

    # Byte 22 (index 13)
    (13, 7, 'switches', 'Handle Switch'),
    (13, 6, 'switches', 'Starter Switch'),
    (13, 5, 'switches', 'Front O2 Rich Signal'),
    (13, 4, 'switches', 'Rear O2 Rich Signal'),
    (13, 3, 'switches', 'Front O2 #2 Rich Signal'),
    (13, 2, 'switches', 'Knock Signal 1'),
    (13, 1, 'switches', 'Knock Signal 2'),
    (13, 0, 'switches', 'Electrical Load Signal'),

    # Byte 23 (index 14)
    (14, 7, 'switches', 'Crank Position Sensor'),
    (14, 6, 'switches', 'Cam Position Sensor'),
    (14, 5, 'switches', 'Defogger Switch'),
    (14, 4, 'switches', 'Blower Switch'),
    (14, 3, 'switches', 'Interior Light Switch'),
    (14, 2, 'switches', 'Wiper Switch'),
    (14, 1, 'switches', 'Air-Con Lock Signal'),
    (14, 0, 'switches', 'Air-Con Mid Pressure Switch'),

    # Byte 24 (index 15)
    (15, 7, 'outputs', 'Air-Con Compressor Signal'),
    (15, 6, 'outputs', 'Radiator Fan Relay #3'),
    (15, 5, 'outputs', 'Radiator Fan Relay #1'),
    (15, 4, 'outputs', 'Radiator Fan Relay #2'),
    (15, 3, 'outputs', 'Fuel Pump Relay'),
    (15, 2, 'outputs', 'Intercooler Auto-Wash Relay'),
    (15, 1, 'outputs', 'CPC Solenoid Valve'),
    (15, 0, 'outputs', 'Blow-By Leak Connector'),

    # Byte 25 (index 16)
    (16, 7, 'outputs', 'PCV Solenoid Valve'),
    (16, 6, 'outputs', 'TGV Output'),
    (16, 5, 'outputs', 'TGV Drive'),
    (16, 4, 'outputs', 'Variable Intake Air Solenoid'),
    (16, 3, 'outputs', 'Pressure Sources Change'),
    (16, 2, 'outputs', 'Vent Solenoid Valve'),
    (16, 1, 'outputs', 'P/S Solenoid Valve'),
    (16, 0, 'outputs', 'Assist Air Solenoid Valve'),

    # Byte 26 (index 17)
    (17, 7, 'outputs', 'Tank Sensor Control Valve'),
    (17, 6, 'outputs', 'Relief Valve Solenoid 1'),
    (17, 5, 'outputs', 'Relief Valve Solenoid 2'),
    (17, 4, 'outputs', 'TCS Relief Valve Solenoid'),
    (17, 3, 'outputs', 'Ex. Gas Positive Pressure'),
    (17, 2, 'outputs', 'Ex. Gas Negative Pressure'),
    (17, 1, 'outputs', 'Intake Air Solenoid'),
    (17, 0, 'outputs', 'Muffler Control'),

    # Byte 27 (index 18)
    (18, 3, 'switches', 'Retard Signal from AT'),
    (18, 2, 'switches', 'Fuel Cut Signal from AT'),
    (18, 1, 'switches', 'Ban of Torque Down'),
    (18, 0, 'switches', 'Request Torque Down VDC'),

    # Byte 28 (index 19)
    (19, 7, 'switches', 'Torque Control Signal #1'),
    (19, 6, 'switches', 'Torque Control Signal #2'),
    (19, 5, 'switches', 'Torque Permission Signal'),
    (19, 4, 'switches', 'EAM Signal'),
    (19, 3, 'switches', 'AT coop. lock up signal'),
    (19, 2, 'switches', 'AT coop. lean burn signal'),
    (19, 1, 'switches', 'AT coop. rich spike signal'),
    (19, 0, 'switches', 'AET Signal'),

    # Byte 39 (index 30)
    (30, 5, 'outputs', 'Throttle Motor Duty'),
    (30, 4, 'sensors', 'Throttle Motor Voltage'),

    # Byte 41 (index 32)
    (32, 7, 'sensors', 'Sub Throttle Sensor'),
    (32, 6, 'sensors', 'Main Throttle Sensor'),
    (32, 5, 'sensors', 'Sub Accelerator Sensor'),
    (32, 4, 'sensors', 'Main Accelerator Sensor'),
    (32, 3, 'sensors', 'Brake Booster Pressure'),
    (32, 2, 'sensors', 'Fuel Pressure (High)'),
    (32, 1, 'sensors', 'Exhaust Gas Temperature'),

    # Byte 42 (index 33)
    (33, 7, 'outputs', 'Cold Start Injector'),
    (33, 6, 'outputs', 'SCV Step'),
    (33, 5, 'sensors', 'Memorized Cruise Speed'),

    # Byte 44 (index 35)
    (35, 7, 'sensors', 'Exhaust VVT Advance Angle Right'),
    (35, 6, 'sensors', 'Exhaust VVT Advance Angle Left'),
    (35, 5, 'outputs', 'Exhaust OCV Duty Right'),
    (35, 4, 'outputs', 'Exhaust OCV Duty Left'),
    (35, 3, 'sensors', 'Exhaust OCV Current Right'),
    (35, 2, 'sensors', 'Exhaust OCV Current Left'),

    # Byte 45 (index 36)
    (36, 6, 'outputs', 'ETC Motor Relay'),

    # Byte 46 (index 37)
    (37, 7, 'switches', 'Clutch Switch'),
    (37, 6, 'switches', 'Stop Light Switch'),
    (37, 5, 'switches', 'Set/Coast Switch'),
    (37, 4, 'switches', 'Resume/Accelerate Switch'),
    (37, 3, 'switches', 'Brake Switch'),
    (37, 1, 'switches', 'Accelerator Switch'),

    # Byte 56 (index 47)
    (47, 7, 'sensors', 'Roughness Monitor Cylinder #1'),
    (47, 6, 'sensors', 'Roughness Monitor Cylinder #2'),
    (47, 5, 'sensors', 'Roughness Monitor Cylinder #3'),
    (47, 4, 'sensors', 'Roughness Monitor Cylinder #4'),
]


def parse_ecu_capabilities(capability_bytes):
    """
    Parse ECU capability bytes into a structured dictionary.

    Args:
        capability_bytes: List of bytes from ECU init response (starting after ECU ID)

    Returns:
        Dictionary with 'sensors', 'switches', and 'outputs' categories
    """
    capabilities = {
        'sensors': {},
        'switches': {},
        'outputs': {}
    }

    def bit_set(byte_val, bit_position):
        """Check if a specific bit is set in a byte value."""
        return bool(byte_val & (1 << bit_position))

    # Parse each capability from the map
    for byte_index, bit_position, category, name in CAPABILITY_MAP:
        if byte_index < len(capability_bytes):
            byte_val = capability_bytes[byte_index]
            capabilities[category][name] = bit_set(byte_val, bit_position)

    return capabilities
