import asyncio
import websockets
from aiohttp import web
import json
import PySSM2
import time
import csv

# SSM2 Handler to log data from the ECU
async def start_ssm2_logger():
    # Initalize our CSV File
    start_time = time.time()
    timestr = time.strftime('%Y%m%d-%H%M%S')
    logfile = open('%s-SubaruLog.csv' % timestr, 'w+')
    logfileheaders = ['Time', 'Boost Pressure', 'Manifold Absolute Pressure', 'Atmospheric Pressure', 'Coolant Temperature', 'A/F Sensor #1', 'Air Fuel Ratio', 'Mass Airflow', 'Vehicle Speed', 'Engine Speed', 'Battery Voltage', 'Fuel Consumption', 'Engine Load']
    lf = csv.DictWriter(logfile, fieldnames= logfileheaders)
    lf.writeheader()
    # Initialize PySSM2
    SSM2 = PySSM2.PySSM2('/dev/ttyUSB0')
    #Initalize the ECU
    SSM2.ecu_init()
    # Request our data from the ECU Continously 
    # Battery Voltage, Coolant Temperature, A/F Sensor #1, Manifold Absolute Pressure, Atmospheric Pressure, Vehicle Speed, Mass Airflow, Engine Speed
    addresses = [0x00001C, 0x000008, 0x000046, 0x00000D, 0x000023, 0x000010, 0x000013, 0x00000E]
    SSM2.read_single_address(addresses)
    while True:
        # We request the length of our address list and then add 6 for heading and checksum bytes
        response = SSM2.receive_packet(len(addresses) + 6)
        battVolt = round(response[5] * 0.08, 1)
        coolent = response[6] - 40
        afr = round(response[7] / 128 * 14.7, 2)
        boost = round((response[8] * 37 / 255) - (response[9] * 37 / 255), 1)
        if response[10] == 0:
            fuelCon = 0
        else:
            fuelCon = (3600/response[10]) * ((response[11] / afr )/761)*100
        if response[12] == 0:
            engineLoad = 0
        else:
            engineLoad = (response[11]*60) / response[12] 
        data = {
            'Time': time.time() - start_time,
            'Boost Pressure': boost,
            'Manifold Absolute Pressure': response[8],
            'Atmospheric Pressure': response[9],
            'Coolant Temperature': coolent,
            'A/F Sensor #1': response[7],
            'Air Fuel Ratio': afr,
            'Mass Airflow': response[11],
            'Vehicle Speed': response[10],
            'Engine Speed': response[12],
            'Battery Voltage': battVolt,
            'Fuel Consumption': fuelCon,
            'Engine Load': engineLoad
        }
        lf.writerow(data)


# WebSocket handler to send multiple values to connected clients
async def websocket_handler(websocket):
            # Send the JSON data to the client
            await websocket.send(json.dumps(data))

            # Print the sent data for debugging
            # print(f"Sent: {data}")
            await asyncio.sleep(0.001)
            # Wait for 1 second before sending the next set of values
            

    # except websockets.ConnectionClosedOK:
    #     print("Client disconnected cleanly")
    # except websockets.ConnectionClosedError:
    #     print("Connection closed with error")
    # except Exception as e:
    #     print(f"An unexpected error occurred: {e}")

# Start WebSocket server
async def start_websocket_server():
    # Bind WebSocket server to 0.0.0.0 to allow connections from any IP
    async with websockets.serve(websocket_handler, "0.0.0.0", 8765):
        await asyncio.Future()  # Run forever

# Start HTTP server
async def handle_root(request):
    return web.FileResponse('./static/index.html')

async def start_http_server():
    app = web.Application()

    # Handle root ('/') to serve index.html
    app.router.add_get('/', handle_root)

    # Serve the entire 'static' folder for all other files (e.g., CSS, JS)
    app.router.add_static('/', './static')

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 80)
    await site.start()
    print("HTTP server started on http://0.0.0.0:80")

# Main function to run both servers concurrently

async def main():
    ssm2_task = asyncio.create_task(start_ssm2_logger())
    websocket_task = asyncio.create_task(start_websocket_server())  # WebSocket server
    http_task = asyncio.create_task(start_http_server())           # HTTP server
    await asyncio.gather(websocket_task, http_task)


if __name__ == "__main__":
    asyncio.run(main())
