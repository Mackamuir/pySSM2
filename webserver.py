# combined_server.py
import asyncio
import websockets
from aiohttp import web
import json
import PySSM2
import time

# WebSocket handler to send multiple values to connected clients
async def websocket_handler(websocket):
    # Initialize PySSM2
    SSM2 = PySSM2.PySSM2('/dev/ttyUSB0')
    #Initalize the ECU
    SSM2.ecu_init()
    # execution_count = 0
    # start_time = time.time()
    # interval = 1
    # Request our data from the ECU Continously 
    # Battery Voltage, Coolant Temperature, A/F Sensor #1, Manifold Absolute Pressure, Atmospheric Pressure, Vehicle Speed, Mass Airflow, Engine Speed
    addresses = [0x00001C, 0x000008, 0x000046, 0x00000D, 0x000023, 0x000010, 0x000013, 0x00000E]
    SSM2.read_single_address(addresses)
    try:
        while True:
            # execution_count += 1
            # elapsed_time = time.time() - start_time
            # if elapsed_time >= interval:
            #     executions_per_second = execution_count / elapsed_time
            #     print(f"Executions per second: {executions_per_second}")
            #     start_time = time.time()
            #     execution_count = 0
            # We request the length of our address list and then 6 for heading and checksum
            response = SSM2.receive_packet(len(addresses) + 6)
            # print(f"{' '.join(hex(n) for n in response)}")
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
                'Boost': boost,
                'CoolentTemp': coolent,
                'BatteryVoltage': battVolt,
                'AirFuel': afr,
                'FuelConsumption': fuelCon,
                'EngineLoad': engineLoad,
            }

            # Send the JSON data to the client
            await websocket.send(json.dumps(data))

            # Print the sent data for debugging
            # print(f"Sent: {data}")
            await asyncio.sleep(0.001)
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
    websocket_task = asyncio.create_task(start_websocket_server())  # WebSocket server
    http_task = asyncio.create_task(start_http_server())           # HTTP server
    await asyncio.gather(websocket_task, http_task)


if __name__ == "__main__":
    asyncio.run(main())
