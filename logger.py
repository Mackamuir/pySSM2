import asyncio
import websockets
from aiohttp import web
import json
import PySSM2
import time
import csv

log_queue = asyncio.Queue()

logfile_timestr = time.strftime('%Y%m%d-%H%M%S')
logfile_name = logfile_timestr + '-SubaruLog.csv'
logfile_location = '/var/log/subaru/' + logfile_name

# SSM2 Handler to log data from the ECU
async def start_ssm2_logger():
    # Initialize PySSM2
    SSM2 = PySSM2.PySSM2('/dev/ttyUSB0')
    #Initalize the ECU
    SSM2.ecu_init()
    # Initalize our CSV File
    start_time = time.time()
    logfile = open(logfile_location, 'w+')
    logfileheaders = ['Time', 'Boost Pressure', 'Manifold Absolute Pressure', 'Atmospheric Pressure', 'Coolant Temperature', 'Air Fuel Ratio', 'Mass Airflow', 'Vehicle Speed', 'Engine Speed', 'Battery Voltage', 'Fuel Consumption', 'Engine Load']
    lf = csv.DictWriter(logfile, fieldnames= logfileheaders)
    lf.writeheader()
    # Request our data from the ECU Continously 
    # Battery Voltage, Coolant Temperature, A/F Sensor #1, Manifold Absolute Pressure, Atmospheric Pressure, Vehicle Speed, Mass Airflow, Engine Speed
    addresses = [0x00001C, 0x000008, 0x000046, 0x00000D, 0x000023, 0x000010, 0x000013, 0x00000E, 0x00000F]
    SSM2.read_single_address(addresses)
    while True:
        # We request the length of our address list and then add 6 for heading and checksum bytes
        response = SSM2.receive_packet(len(addresses) + 6)
        batteryVoltage = round(response[5] * 0.08, 1)
        coolentTemperature = response[6] - 40 # Celcius
        airFuelRatio = round(response[7] / 128 * 14.7, 2)
        ManifoldAbsolutePressure = response[8] * 37 / 255
        atmosphericPressure = response[9] * 37 / 255 # PSI
        vehicleSpeed = response[10]
        massAirflow = response[11] / 100
        boostPressure = round(ManifoldAbsolutePressure - atmosphericPressure, 1)
        engineSpeed = int(str(response[12]) + str(response[13])) / 4
        if vehicleSpeed == 0:
            fuelConsumption = round((1) * ((massAirflow / airFuelRatio ) /761 ) * 100, 1)
        else:
            fuelConsumption = round((3600 / vehicleSpeed) * ((massAirflow / airFuelRatio ) / 761) * 100,1 )
        if engineSpeed == 0:
            engineLoad = 0
        else:
            engineLoad = (massAirflow * 60) / engineSpeed
        data = {
            'Time': time.time() - start_time,
            'Boost Pressure': boostPressure,
            'Manifold Absolute Pressure': ManifoldAbsolutePressure,
            'Atmospheric Pressure': atmosphericPressure,
            'Coolant Temperature': coolentTemperature,
            'Air Fuel Ratio': airFuelRatio,
            'Mass Airflow': massAirflow,
            'Vehicle Speed': vehicleSpeed,
            'Engine Speed': engineSpeed,
            'Battery Voltage': batteryVoltage,
            'Fuel Consumption': fuelConsumption,
            'Engine Load': engineLoad
        }
        await log_queue.put(data)
        lf.writerow(data)
        await asyncio.sleep(0.001)


# WebSocket handler to send multiple values to connected clients
async def websocket_handler(websocket):
    try:
        while True:
            # Read Last Line from 
            # Send the JSON data to the client
            logdata = await log_queue.get()
            wsdata = {
                'Boost': logdata.get('Boost Pressure'),
                'CoolentTemp': logdata.get('Coolant Temperature'),
                'AirFuel': logdata.get('Air Fuel Ratio'),
                'BatteryVoltage': logdata.get('Battery Voltage'),
                'FuelConsumption': logdata.get('Fuel Consumption'),
                'EngineLoad': logdata.get('Engine Load')
            }
            await websocket.send(json.dumps(wsdata))

            # Print the sent data for debugging
            # print(f"Sent: {data}")
            await asyncio.sleep(0.007)
            # Wait for 1 second before sending the next set of values
    except websockets.ConnectionClosedOK:
        print("Client disconnected cleanly")
    except websockets.ConnectionClosedError:
        print("Connection closed with error")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

# Start WebSocket server
async def start_websocket_server():
    # Bind WebSocket server to 0.0.0.0 to allow connections from any IP
    async with websockets.serve(websocket_handler, "0.0.0.0", 8765):
        await asyncio.Future()  # Run forever

# Start HTTP server
async def handle_root(request):
    return web.FileResponse('/etc/pySSM2/static/index.html')

async def start_http_server():
    app = web.Application()

    # Handle root ('/') to serve index.html
    app.router.add_get('/', handle_root)

    # Serve the entire 'static' folder for all other files (e.g., CSS, JS)
    app.router.add_static('/', '/etc/pySSM2/static')
    # Serve our log files for easy downloading
    app.router.add_static('/logs', '/var/log/subaru/')
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 80)
    await site.start()
    print("HTTP server started on http://0.0.0.0:80")

# Main function to run both servers concurrently

async def main():
    http_task = asyncio.create_task(start_http_server()) # HTTP server
    SSM2_logger_task = asyncio.create_task(start_ssm2_logger())  # SSM2 Logger 
    websocket_task = asyncio.create_task(start_websocket_server())  # WebSocket server
    await asyncio.gather(websocket_task, http_task, SSM2_logger_task)


if __name__ == "__main__":
    asyncio.run(main())

