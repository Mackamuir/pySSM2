import asyncio
import json
import PySSM2
import time
import csv
import serial
import logging
from typing import Dict, Any

# Import configuration
import config

# Import display
from gui import run_display

# ============================================================================
# LOGGING SETUP
# ============================================================================

def setup_logging():
    """
    Configure Python logging with file handlers and rotation.

    Creates multiple log files:
    - pySSM2.log: All messages (INFO and above)
    - pySSM2-error.log: Only ERROR and CRITICAL messages
    - pySSM2-debug.log: All DEBUG messages (if DEBUG_MODE enabled)

    Uses RotatingFileHandler to prevent log files from growing too large.
    """
    from logging.handlers import RotatingFileHandler

    # Create logger
    logger = logging.getLogger('pySSM2')
    logger.setLevel(logging.DEBUG if config.DEBUG_MODE else getattr(logging, config.LOG_LEVEL))

    # Clear any existing handlers
    logger.handlers.clear()

    # Formatter for log messages
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Console handler (always enabled)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, config.LOG_LEVEL))
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handlers (if enabled)
    if config.ENABLE_PYTHON_LOGGING:
        try:
            log_paths = config.get_python_log_paths()

            # Handler for all messages (INFO and above)
            all_handler = RotatingFileHandler(
                log_paths['all'],
                maxBytes=config.LOG_FILE_MAX_BYTES,
                backupCount=config.LOG_FILE_BACKUP_COUNT
            )
            all_handler.setLevel(logging.INFO)
            all_handler.setFormatter(formatter)
            logger.addHandler(all_handler)

            # Handler for errors only (ERROR and CRITICAL)
            error_handler = RotatingFileHandler(
                log_paths['error'],
                maxBytes=config.LOG_FILE_MAX_BYTES,
                backupCount=config.LOG_FILE_BACKUP_COUNT
            )
            error_handler.setLevel(logging.ERROR)
            error_handler.setFormatter(formatter)
            logger.addHandler(error_handler)

            # Handler for debug (only if debug mode enabled)
            if config.DEBUG_MODE:
                debug_handler = RotatingFileHandler(
                    log_paths['debug'],
                    maxBytes=config.LOG_FILE_MAX_BYTES,
                    backupCount=config.LOG_FILE_BACKUP_COUNT
                )
                debug_handler.setLevel(logging.DEBUG)
                debug_handler.setFormatter(formatter)
                logger.addHandler(debug_handler)

            logger.info(f"Python logging enabled: {log_paths['all']}")

        except (OSError, IOError) as e:
            # If file logging fails, warn but continue with console only
            logger.warning(f"Failed to setup file logging: {e}")
            logger.warning("Continuing with console logging only")

    return logger

# Setup logging
logger = setup_logging()

# Validate configuration on startup
try:
    config.validate_config()
    if config.DEBUG_MODE:
        config.print_config()
except ValueError as e:
    logger.error(f"Configuration error: {e}")
    exit(1)

# ============================================================================
# ECU ADDRESS CONFIGURATION
# ============================================================================
# Each entry defines an ECU parameter to monitor.
# - 'address': ECU memory address (or list of addresses for multi-byte values)
# - 'name': Human-readable name for logging/display
# - 'calculation': Function that converts raw byte(s) to final value
# - 'format': Optional format string for output (default: no formatting)
# - 'unit': Optional unit string for documentation
# ============================================================================

ECU_PARAMETERS = [
    {
        'address': 0x00001C,
        'name': 'Battery Voltage',
        'calculation': lambda raw: float(raw[0] * 0.08),
        'format': '.1f',
        'unit': 'V'
    },
    {
        'address': 0x000008,
        'name': 'Coolant Temperature',
        'calculation': lambda raw: raw[0] - 40,
        'format': None,
        'unit': 'C'
    },
    {
        'address': 0x000046,
        'name': 'Air Fuel Ratio',
        'calculation': lambda raw: float(raw[0] / 128 * 14.7),
        'format': '.2f',
        'unit': 'AFR'
    },
    {
        'address': 0x00000D,
        'name': 'Manifold Absolute Pressure',
        'calculation': lambda raw: float(raw[0] * 37 / 255),
        'format': '.2f',
        'unit': 'PSI'
    },
    {
        'address': 0x000023,
        'name': 'Atmospheric Pressure',
        'calculation': lambda raw: float(raw[0] * 37 / 255),
        'format': '.3f',
        'unit': 'PSI'
    },
    {
        'address': 0x000010,
        'name': 'Vehicle Speed',
        'calculation': lambda raw: float(raw[0]),
        'format': None,
        'unit': 'km/h'
    },
    {
        'address': [0x000013, 0x000014],  # 16-bit value
        'name': 'Mass Airflow',
        'calculation': lambda raw: float(((raw[0] << 8) | raw[1]) / 100),
        'format': '.2f',
        'unit': 'g/s'
    },
    {
        'address': [0x00000E, 0x00000F],  # 16-bit value
        'name': 'Engine Speed',
        'calculation': lambda raw: float(((raw[0] << 8) | raw[1]) / 4),
        'format': None,
        'unit': 'RPM'
    },
]

# Derived parameters calculated from ECU parameters
DERIVED_PARAMETERS = [
    {
        'name': 'Boost Pressure',
        'calculation': lambda data: data['Manifold Absolute Pressure'] - data['Atmospheric Pressure'],
        'format': '.1f',
        'unit': 'PSI'
    },
    {
        'name': 'Fuel Consumption',
        'calculation': lambda data: (
            float((1) * ((data['Mass Airflow'] / data['Air Fuel Ratio']) / 761) * 100)
            if data['Vehicle Speed'] == 0
            else float((3600 / data['Vehicle Speed']) * ((data['Mass Airflow'] / data['Air Fuel Ratio']) / 761) * 100)
        ),
        'format': '.1f',
        'unit': 'L/100km'
    },
    {
        'name': 'Engine Load',
        'calculation': lambda data: (
            0 if data['Engine Speed'] == 0
            else (data['Mass Airflow'] * 60) / data['Engine Speed']
        ),
        'format': None,
        'unit': None
    },
]

# Helper function to extract raw bytes from response
def extract_raw_bytes(response, start_index=5):
    """
    Extract and parse raw bytes from ECU response based on parameter configuration.
    Returns dict of parameter names to their calculated (unformatted) values.
    """
    raw_data = {}
    response_index = start_index

    for param in ECU_PARAMETERS:
        # Extract raw bytes for this parameter
        if isinstance(param['address'], list):
            # Multi-byte value
            num_bytes = len(param['address'])
            raw_bytes = response[response_index:response_index + num_bytes]
            response_index += num_bytes
        else:
            # Single byte value
            raw_bytes = [response[response_index]]
            response_index += 1

        # Calculate value using the parameter's calculation function
        raw_data[param['name']] = param['calculation'](raw_bytes)

    return raw_data


def format_value(value, format_string):
    """
    Format a value according to format string, or return as-is if no format specified.
    """
    if format_string:
        return f"{value:{format_string}}"
    return value


def build_address_list():
    """
    Build flat list of ECU addresses from configuration.
    Multi-byte addresses are flattened into individual address entries.
    """
    addresses = []
    for param in ECU_PARAMETERS:
        if isinstance(param['address'], list):
            addresses.extend(param['address'])
        else:
            addresses.append(param['address'])
    return addresses


# SSM2 Handler to log data from the ECU
async def start_ssm2_logger(csv_queue: asyncio.Queue, latest_data: Dict[str, Any]):
    """
    Read data from ECU and publish to both CSV queue and latest_data dict.

    Args:
        csv_queue: Queue for CSV writer (preserves order, never drops data)
        latest_data: Shared dict for display (always latest, can skip old data)
    """
    logger.info("Starting SSM2 logger...")

    try:
        # Auto-scan for K-Line adapter (run in executor so display keeps updating)
        logger.info("Scanning for K-Line adapter...")
        loop = asyncio.get_event_loop()
        port = await loop.run_in_executor(
            None,
            lambda: PySSM2.PySSM2.scan_for_adapter(
                baudrate=config.SERIAL_BAUDRATE,
                timeout=config.SERIAL_TIMEOUT,
                status=latest_data,
            ),
        )
        logger.info(f"K-Line adapter found on {port}")

        # Initialize PySSM2
        logger.info(f"Connecting to ECU on {port} at {config.SERIAL_BAUDRATE} baud")
        SSM2 = PySSM2.PySSM2(
            port,
            baudrate=config.SERIAL_BAUDRATE,
            timeout=config.SERIAL_TIMEOUT
        )

        # Initialize the ECU
        SSM2.ecu_init()
        logger.info("ECU initialized successfully")

        # Build address list from configuration
        addresses = build_address_list()
        logger.debug(f"Monitoring {len(ECU_PARAMETERS)} ECU parameters")

        # Start continuous reading
        SSM2.read_single_address_continuously(addresses)

        while True:
            try:
                # We request the length of our address list and then add 6 for heading and checksum bytes
                response = SSM2.receive_packet(len(addresses) + 6)

                # Parse response once to get raw calculated values
                raw_data = extract_raw_bytes(response, start_index=5)

                # Build logdata with formatted values
                logdata = {'Time': time.time()}

                # Add ECU parameters with formatting
                for param in ECU_PARAMETERS:
                    value = raw_data[param['name']]
                    logdata[param['name']] = format_value(value, param['format'])

                # Calculate and add derived parameters
                for derived in DERIVED_PARAMETERS:
                    value = derived['calculation'](raw_data)
                    logdata[derived['name']] = format_value(value, derived['format'])

                # Publish to CSV queue (preserves all data in order)
                if config.ENABLE_CSV_LOGGING:
                    try:
                        csv_queue.put_nowait(logdata)
                    except asyncio.QueueFull:
                        logger.warning("CSV queue full, dropping oldest data")
                        # Remove old data and add new
                        try:
                            csv_queue.get_nowait()
                            csv_queue.put_nowait(logdata)
                        except asyncio.QueueEmpty:
                            pass

                # Update latest data for display (always latest, no queue)
                latest_data.clear()
                latest_data.update(logdata)

            except (TimeoutError, IndexError) as e:
                logger.error(f"Error reading ECU data: {e}")
                await asyncio.sleep(1)  # Wait before retrying
                continue
            except ZeroDivisionError as e:
                logger.warning(f"Math error in calculations (likely zero division): {e}")
                # Continue with next iteration, don't publish invalid data
                continue
            except Exception as e:
                logger.error(f"Unexpected error processing ECU data: {e}", exc_info=config.DEBUG_MODE)
                await asyncio.sleep(1)
                continue

            await asyncio.sleep(config.LOGGER_SLEEP_INTERVAL)

    except serial.SerialException as e:
        logger.critical(f"Serial port error: {e}")
        logger.critical(f"Check that {config.SERIAL_PORT} exists and is accessible.")
    except Exception as e:
        logger.critical(f"Fatal error in SSM2 logger: {e}", exc_info=True)

# Helper function to build CSV headers from configuration
def build_csv_headers():
    """
    Build list of CSV column headers from ECU and derived parameter configurations.
    """
    headers = ['Time']
    headers.extend([param['name'] for param in ECU_PARAMETERS])
    headers.extend([param['name'] for param in DERIVED_PARAMETERS])
    return headers


# Write the data to the CSV File
async def write_to_csv(csv_queue: asyncio.Queue):
    """
    Read data from queue and write to CSV file.
    Queue ensures all data is preserved in correct time order.

    Args:
        csv_queue: Async queue to consume log data from (FIFO order)
    """
    if not config.ENABLE_CSV_LOGGING:
        logger.info("CSV logging disabled in configuration")
        return

    log_file_path = config.get_log_file_path()
    logger.info(f"Starting CSV logger: {log_file_path}")

    try:
        # Use context manager to ensure file is properly closed
        with open(log_file_path, 'w', newline='') as logfile:
            # Build CSV headers from configuration
            logfileheaders = build_csv_headers()

            lf = csv.DictWriter(logfile, fieldnames=logfileheaders)
            lf.writeheader()

            last_data = None
            while True:
                try:
                    # Wait for data from queue with timeout
                    # Queue preserves order (FIFO) so CSV is always chronological
                    data = await asyncio.wait_for(csv_queue.get(), timeout=1.0)

                    # Only write if data has changed
                    if data != last_data:
                        try:
                            lf.writerow(data)
                            logfile.flush()  # Ensure data is written immediately
                            last_data = data
                        except (ValueError, KeyError) as e:
                            logger.error(f"Error writing CSV row: {e}")

                except asyncio.TimeoutError:
                    # No data received, continue waiting
                    pass

                await asyncio.sleep(config.CSV_WRITER_SLEEP_INTERVAL)

    except IOError as e:
        logger.error(f"Error opening CSV file {log_file_path}: {e}")
        logger.error(f"CSV logging disabled. Check that {config.LOG_DIRECTORY} exists.")
    except Exception as e:
        logger.error(f"Unexpected error in CSV writer: {e}", exc_info=config.DEBUG_MODE)


# Main function to run all services concurrently
async def main():
    """
    Main entry point - starts all async tasks.

    Data flow:
    - CSV queue: FIFO queue, preserves all data in order for accurate logging
    - latest_data dict: Shared dict, always has newest data for live display
    """
    logger.info("=" * 70)
    logger.info("pySSM2 Logger Starting")
    logger.info("=" * 70)

    # Create CSV queue (FIFO - preserves order, never drops data unless full)
    csv_queue = asyncio.Queue(maxsize=1000)

    # Create shared dict for latest data (display always gets newest, skips old)
    latest_data: Dict[str, Any] = {}

    # Create tasks for all services
    tasks = [
        asyncio.create_task(run_display(
            latest_data=latest_data,
            display_width=config.DISPLAY_WIDTH,
            display_height=config.DISPLAY_HEIGHT,
            fullscreen=config.DISPLAY_FULLSCREEN,
            target_fps=config.DISPLAY_FPS,
        ), name="Display"),
        asyncio.create_task(start_ssm2_logger(csv_queue, latest_data), name="SSM2 Logger"),
        asyncio.create_task(write_to_csv(csv_queue), name="CSV Writer"),
    ]

    logger.info(f"Started {len(tasks)} services")
    logger.info("Display: pygame dashboard")
    logger.info("CSV: Queue-based (preserves order)")

    try:
        # Run all tasks concurrently
        await asyncio.gather(*tasks, return_exceptions=True)
    except KeyboardInterrupt:
        logger.info("Shutting down gracefully...")
    except Exception as e:
        logger.critical(f"Fatal error in main: {e}", exc_info=True)
    finally:
        logger.info("pySSM2 Logger stopped")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
        pass
