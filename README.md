# pySSM2

A Python-based interface for Subaru ECUs using the SSM2 protocol. This project enables real-time data logging and visualization from Subaru vehicles through a web interface.

This project has a long way to go before being user friendly (or well written), I would only recommend using this if you have a basic knowledge of python or are just willing to use what I have done

## Setup
This will be going over how I have this setup in my car.

### Equipment
- Raspberry Pi
- Raspberry Pi UPS Hat (I use this one https://core-electronics.com.au/raspberry-pi-5-18650-battery-ups-hat-51v-5a.html)
- K-Line Adapter (I just picked one up off ali-express)
- USB NIC (Make sure it's supported out of the box by the rpi, so you don't need to go through the driver debacle I had to.)

### My Setup

I currently use a Raspberry Pi 5 that is mounted in the glove box, If you are planning on doing this I would recommend a 4B as they can output Video over the 3.5mm jack to your radio and then a service to launch firefox or chrome on boot and display (I've included one in the services folder). Alternatively you can mount your phone or something to your dash.

I set up the rPi as a wifi hotspot so I'm able to connect devices to it and view the current statistics.



## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/pySSM2.git
cd pySSM2
```

2. Install dependencies:
```bash
pip install pyserial aiohttp websockets
```

3. Ensure proper file permissions:
```bash
sudo chmod +x update.sh
```

## Usage

1. Connect your SSM2 interface to your vehicle's OBD port

2. Run the logger:
```bash
python3 logger.py
```

3. Access the web interface at `http://<your-ip-address>`

## File Structure

- `PySSM2.py` - Core SSM2 protocol implementation
- `logger.py` - Main application and web server
- `static/` - Web interface files
- `update.sh` - Installation helper script

## License

This project is licensed under the GNU General Public License v3.0 - see the LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit pull requests.
