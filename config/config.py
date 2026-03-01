#!/usr/bin/env python3
"""
Configuration file for pySSM2 logger.

This file centralizes all configuration settings. Values can be overridden
using environment variables (see README.md for details).
"""

import os


# ============================================================================
# SERIAL PORT CONFIGURATION
# ============================================================================

# Serial port device path
SERIAL_PORT = os.getenv('SSM2_SERIAL_PORT', '/dev/ttyUSB0')

# Serial baud rate (SSM2 standard is 4800)
SERIAL_BAUDRATE = int(os.getenv('SSM2_BAUDRATE', '4800'))

# Serial timeout in seconds
SERIAL_TIMEOUT = int(os.getenv('SSM2_TIMEOUT', '2'))


# ============================================================================
# NETWORK CONFIGURATION
# ============================================================================

# WebSocket server host (0.0.0.0 = all interfaces)
WEBSOCKET_HOST = os.getenv('SSM2_WS_HOST', '0.0.0.0')

# WebSocket server port
WEBSOCKET_PORT = int(os.getenv('SSM2_WS_PORT', '8765'))

# HTTP server host (0.0.0.0 = all interfaces)
HTTP_HOST = os.getenv('SSM2_HTTP_HOST', '0.0.0.0')

# HTTP server port
HTTP_PORT = int(os.getenv('SSM2_HTTP_PORT', '80'))


# ============================================================================
# FILE PATHS
# ============================================================================

# Directory for CSV log files
LOG_DIRECTORY = os.getenv('SSM2_LOG_DIR', '/var/log/subaru/')

# Directory containing static web files
STATIC_DIRECTORY = os.getenv('SSM2_STATIC_DIR', '/etc/pySSM2/static')

# Path to index.html
INDEX_HTML_PATH = os.getenv('SSM2_INDEX_HTML', '/etc/pySSM2/static/index.html')


# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================

# Enable CSV logging
ENABLE_CSV_LOGGING = os.getenv('SSM2_ENABLE_CSV', 'true').lower() == 'true'

# CSV filename format (uses strftime format)
CSV_FILENAME_FORMAT = os.getenv('SSM2_CSV_FORMAT', '%Y%m%d-%H%M%S-SubaruLog.csv')

# Enable debug output
DEBUG_MODE = os.getenv('SSM2_DEBUG', 'false').lower() == 'true'

# Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
LOG_LEVEL = os.getenv('SSM2_LOG_LEVEL', 'INFO')

# Python application logging configuration
ENABLE_PYTHON_LOGGING = os.getenv('SSM2_ENABLE_PYTHON_LOGS', 'true').lower() == 'true'

# Python log directory (separate from CSV data logs)
PYTHON_LOG_DIRECTORY = os.getenv('SSM2_PYTHON_LOG_DIR', '/var/log/subaru/python/')

# Maximum log file size before rotation (in bytes, default 10MB)
LOG_FILE_MAX_BYTES = int(os.getenv('SSM2_LOG_MAX_BYTES', str(10 * 1024 * 1024)))

# Number of backup log files to keep
LOG_FILE_BACKUP_COUNT = int(os.getenv('SSM2_LOG_BACKUP_COUNT', '5'))


# ============================================================================
# PERFORMANCE TUNING
# ============================================================================

# Sleep interval in main logger loop (seconds)
LOGGER_SLEEP_INTERVAL = float(os.getenv('SSM2_LOGGER_SLEEP', '0.001'))

# Sleep interval in CSV writer loop (seconds)
CSV_WRITER_SLEEP_INTERVAL = float(os.getenv('SSM2_CSV_SLEEP', '0.001'))

# Sleep interval in WebSocket loop (seconds)
WEBSOCKET_SLEEP_INTERVAL = float(os.getenv('SSM2_WS_SLEEP', '0.001'))


# ============================================================================
# WEBSOCKET DATA MAPPING
# ============================================================================
# Maps internal parameter names to WebSocket field names
# This allows customizing the WebSocket payload structure without changing core code

WEBSOCKET_FIELD_MAPPING = {
    'Boost Pressure': 'Boost',
    'Coolant Temperature': 'CoolentTemp',
    'Air Fuel Ratio': 'AirFuel',
    'Battery Voltage': 'BatteryVoltage',
    'Fuel Consumption': 'FuelConsumption',
    'Engine Load': 'EngineLoad',
}


# ============================================================================
# VALIDATION
# ============================================================================

def validate_config():
    """
    Validate configuration settings and provide helpful error messages.
    Returns True if valid, raises ValueError if invalid.
    """
    import os.path

    # Check that base log directory exists if CSV logging is enabled
    # Subdirectories (YYYY/Month/DD/) will be created automatically
    if ENABLE_CSV_LOGGING and not os.path.exists(LOG_DIRECTORY):
        raise ValueError(
            f"CSV logging enabled but base log directory does not exist: {LOG_DIRECTORY}\n"
            f"Create it with: sudo mkdir -p {LOG_DIRECTORY}\n"
            f"Note: Date-based subdirectories (YYYY/Month/DD/) will be created automatically."
        )

    # Check that static directory exists
    if not os.path.exists(STATIC_DIRECTORY):
        print(f"WARNING: Static directory does not exist: {STATIC_DIRECTORY}")
        print("Web interface may not work correctly.")

    # Validate port numbers
    if not (1 <= WEBSOCKET_PORT <= 65535):
        raise ValueError(f"Invalid WebSocket port: {WEBSOCKET_PORT}")

    if not (1 <= HTTP_PORT <= 65535):
        raise ValueError(f"Invalid HTTP port: {HTTP_PORT}")

    # Warn if running on privileged port without root
    if HTTP_PORT < 1024 and os.geteuid() != 0:
        print(f"WARNING: HTTP port {HTTP_PORT} requires root privileges")
        print("Run with sudo or change HTTP_PORT to >= 1024")

    return True


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_log_file_path():
    """
    Generate the full path for the current CSV log file.
    Creates a hierarchical directory structure: YYYY/Month/DD/
    Example: /var/log/subaru/2025/October/24/20251024-143022-SubaruLog.csv
    """
    import time
    import calendar

    # Get current date components
    now = time.localtime()
    year = str(now.tm_year)
    month = calendar.month_name[now.tm_mon]  # Full month name (e.g., "October")
    day = str(now.tm_mday).zfill(2)  # Zero-padded day (e.g., "24")

    # Build directory path: LOG_DIRECTORY/YYYY/MonthName/DD/
    log_dir = os.path.join(LOG_DIRECTORY, year, month, day)

    # Create directory structure if it doesn't exist
    os.makedirs(log_dir, exist_ok=True)

    # Generate filename using configured format
    filename = time.strftime(CSV_FILENAME_FORMAT)

    return os.path.join(log_dir, filename)


def get_python_log_directory():
    """
    Get the directory for Python application logs for the current date.
    Creates a hierarchical directory structure: YYYY/Month/DD/
    Example: /var/log/subaru/python/2025/October/24/
    """
    import time
    import calendar

    # Get current date components
    now = time.localtime()
    year = str(now.tm_year)
    month = calendar.month_name[now.tm_mon]
    day = str(now.tm_mday).zfill(2)

    # Build directory path
    log_dir = os.path.join(PYTHON_LOG_DIRECTORY, year, month, day)

    # Create directory structure if it doesn't exist
    os.makedirs(log_dir, exist_ok=True)

    return log_dir


def get_python_log_paths():
    """
    Get full paths for Python log files.
    Returns dict with paths for different log types.
    """
    import time

    log_dir = get_python_log_directory()
    date_str = time.strftime('%Y%m%d')

    return {
        'all': os.path.join(log_dir, f'{date_str}-pySSM2.log'),
        'error': os.path.join(log_dir, f'{date_str}-pySSM2-error.log'),
        'debug': os.path.join(log_dir, f'{date_str}-pySSM2-debug.log')
    }


def get_log_files_tree():
    """
    Get a nested dictionary representing the log directory structure.
    Returns: dict with years -> months -> days -> [files]
    Example: {'2025': {'October': {'24': ['20251024-143022-SubaruLog.csv', ...]}}}
    """
    import os
    from collections import defaultdict

    tree = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))

    if not os.path.exists(LOG_DIRECTORY):
        return {}

    # Walk through the directory structure
    for year_dir in os.listdir(LOG_DIRECTORY):
        year_path = os.path.join(LOG_DIRECTORY, year_dir)
        if not os.path.isdir(year_path):
            continue

        for month_dir in os.listdir(year_path):
            month_path = os.path.join(year_path, month_dir)
            if not os.path.isdir(month_path):
                continue

            for day_dir in os.listdir(month_path):
                day_path = os.path.join(month_path, day_dir)
                if not os.path.isdir(day_path):
                    continue

                # Get all CSV files in this day directory
                files = [f for f in os.listdir(day_path) if f.endswith('.csv')]
                if files:
                    tree[year_dir][month_dir][day_dir] = sorted(files)

    return dict(tree)


def print_config():
    """
    Print current configuration (useful for debugging).
    """
    print("=" * 70)
    print("pySSM2 Logger Configuration")
    print("=" * 70)
    print(f"Serial Port:        {SERIAL_PORT}")
    print(f"Baud Rate:          {SERIAL_BAUDRATE}")
    print(f"WebSocket:          {WEBSOCKET_HOST}:{WEBSOCKET_PORT}")
    print(f"HTTP Server:        {HTTP_HOST}:{HTTP_PORT}")
    print(f"CSV Logging:        {'Enabled' if ENABLE_CSV_LOGGING else 'Disabled'}")
    if ENABLE_CSV_LOGGING:
        print(f"Log Directory:      {LOG_DIRECTORY}")
        print(f"Current Log File:   {get_log_file_path()}")
        print(f"Log Structure:      YYYY/MonthName/DD/")
    print(f"Static Files:       {STATIC_DIRECTORY}")
    print(f"Debug Mode:         {'Enabled' if DEBUG_MODE else 'Disabled'}")
    print(f"Log Level:          {LOG_LEVEL}")
    print("=" * 70)


if __name__ == "__main__":
    # When run directly, print configuration and validate
    print_config()
    try:
        validate_config()
        print("\nConfiguration is valid")
    except ValueError as e:
        print(f"\nConfiguration error: {e}")
        exit(1)
