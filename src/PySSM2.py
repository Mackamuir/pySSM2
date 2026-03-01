import serial
import struct
import time
from ecu_capabilities import parse_ecu_capabilities

class PySSM2:
    def __init__(self, port, baudrate=4800, timeout=2):
        """
        Initialize the SSM2Protocol class with the default serial communication settings.
        """
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.source = 0xF0  # Default source address (Diagnostic Tool)
        self.destination = 0x10  # Destination address (Subaru ECU)
        self.ser = serial.Serial(port, baudrate=baudrate, timeout=timeout)  # Initialize serial connection

    def calculate_checksum(self, packet):
        """
        Calculate the checksum by summing all bytes and taking the least significant byte.
        """
        return sum(packet) & 0xFF

    def send_packet(self, data, responseLength=1024):
        """
        Send a packet constructed using the SSM2 protocol. It includes the header, data, and checksum.
        """
        # Construct the packet with a header (0x80, destination, source, data length), data, and checksum
        packet = [0x80, self.destination, self.source,  len(data)] + data
        packet.append(self.calculate_checksum(packet))  # Append the calculated checksum
        # Send the packet via the serial port
        self.ser.write(bytearray(packet))   
        response = self.receive_packet(len(packet) + responseLength)
        response = response[len(packet):]
        if not response:
            raise TimeoutError("No response received from ECU.")
        return response
    
    def receive_packet(self, responseLength):
        response = self.ser.read(responseLength)
        # DEBUG
        print("---")
        print("Packet Read:")
        print(response[1])
        print(f"Returned Number of Bytes: {len(response)}")
        print(f"Expected Returned Number of Bytes: {responseLength}")
        print(f"Full Hex String: {' '.join(hex(n) for n in response)}")
        print(f"Start Byte: {hex(response[0])}")
        print(f"Destination Byte: {hex(response[1])}")
        print(f"Source Byte: {hex(response[2])}")
        print(f"Data Size Byte: {hex(response[3])}")
        print(f"Data Size Int: {response[3]}")
        datalen = int(response[3])
        print(f"Data Bytes Hex: {' '.join(hex(n) for n in response[4:4 + datalen])}")
        print(f"Data Bytes Int: {list(response[4:4 + datalen])}")
        print(f"Expected Checksum: {hex(self.calculate_checksum(response[:4 + datalen]))}")
        print(f"Returned Checksum: {response[4 + datalen: 5 + datalen].hex()}")
        # DEBUG
        if not response:
            raise Exception("No response received from ECU.")
        return list(response)


    def receive_packets_continuously(self, responseLength):
        response = self.ser.read(responseLength)

        if not response:
            raise TimeoutError("No response received from ECU.")
        return list(response)
         
    def read_memory(self, address, byte_count):
        """
        Read a block of memory starting from the given address.
        """
        # print("Read Block Address (Write):")
        # Construct the command for reading memory using 0xA0 and the memory address
        try:
            data = [0xA0, 0x00] + list(struct.pack('>I', address)[1:]) + [byte_count - 1]
            return self.send_packet(data)
        except Exception as e:
            print("Error Reading from the ECU, ERROR:")
            print(e)

    def read_single_address(self, addresses):
        """
        Read values from one or more specific addresses.
        Each address should be a 3-byte value.
        """
        # Calculate How long our response should be, Each address asked for should return 1 byte, add 6 bytes for all other packet data
        responseLength = len(addresses) + 6
        # Construct the command for reading single addresses using 0xA8.
        # Each address is packed as 3 bytes.
        data = [0xA8, 0x00]  # Byte for reading single address + single read mode byte
        for address in addresses:
            # Pack each address as a 3-byte integer (use the last 3 bytes of a 4-byte integer)
            data += list(struct.pack('>I', address)[1:])  # Exclude the first byte (since we're only using 3 bytes)
        # print("Read Single Address:")
        return self.send_packet(data, responseLength)

    def read_single_address_continuously(self, addresses):
        """
        Read values from one or more specific addresses.
        Each address should be a 3-byte value.
        """
        # Calculate How long our response should be, Each address asked for should return 1 byte, add 6 bytes for all other packet data
        responseLength = len(addresses) + 6
        # Construct the command for reading single addresses using 0xA8.
        # Each address is packed as 3 bytes.
        data = [0xA8, 0x01]  # Byte for reading single address + continious read mode byte 
        for address in addresses:
            # Pack each address as a 3-byte integer (use the last 3 bytes of a 4-byte integer)
            data += list(struct.pack('>I', address)[1:])  # Exclude the first byte (since we're only using 3 bytes)
        # print("Read Single Address:")
        return self.send_packet(data, responseLength)
    
    def write_memory(self, address, values):
        """
        Write a block of memory starting from the given address.
        """
        # Construct the command for writing memory using 0xB0 and the memory address
        try:
            data = [0xB0] + list(struct.pack('>I', address)[1:]) + values
            return self.send_packet(data)
        except Exception as e:
            print("(write_memory) Error Writing to the ECU, ERROR:")
            print(e)

    def write_single_address(self, address, value):
        """
        Write a single byte to a specific address.
        """
        # Construct the command for writing a single address using 0xB8
        data = [0xB8] + list(struct.pack('>I', address)[1:]) + [value]
        # print("Write Single Address:")
        return self.send_packet(data)

    def parse_ecu_init(self, response):
        """
        Parse the ECU initialization response to extract ECU ID and capability flags.

        Returns a dictionary containing:
        - ecu_id: 5-byte ECU identifier
        - capabilities: dictionary of supported parameters organized by category
        - raw_capability_bytes: raw capability flag bytes for manual inspection
        """
        if len(response) < 13:
            raise ValueError(f"ECU init response too short: {len(response)} bytes")

        # Extract ECU ID (5 bytes starting at index 8 in the full response)
        # Response structure: [0x80, dest, source, data_len, 0xFF, ..., ECU_ID[5 bytes], capability_flags...]
        ecu_id = response[8:13]

        # Extract capability bytes (starting at byte 9 after ECU ID, which is index 13 in response)
        capability_bytes = response[13:] if len(response) > 13 else []

        # Parse capabilities using the external module
        capabilities = parse_ecu_capabilities(capability_bytes)

        return {
            'ecu_id': ecu_id,
            'ecu_id_hex': ' '.join(hex(b) for b in ecu_id),
            'capabilities': capabilities,
            'raw_capability_bytes': capability_bytes
        }

    def ecu_init(self):
        """
        Send an ECU initialization request and return the response.
        """
        print("Initializing ECU, Please Wait...")
        data = [0xBF]
        initialized = False
        self.ser.flush()
        while not initialized:
            try:
                response = self.send_packet(data) # We're not going to bother asking for the amount of bytes as each subaru is different
                # Parse the ECU init response
                ecu_info = self.parse_ecu_init(response)
                print(f"ECU Initialized, ECU ID is: {ecu_info['ecu_id_hex']}")

                # Count supported features
                total_sensors = sum(1 for v in ecu_info['capabilities']['sensors'].values() if v)
                total_switches = sum(1 for v in ecu_info['capabilities']['switches'].values() if v)
                total_outputs = sum(1 for v in ecu_info['capabilities']['outputs'].values() if v)
                print(f"ECU Capabilities: {total_sensors} sensors, {total_switches} switches, {total_outputs} outputs")

                initialized = True
                return ecu_info
            except Exception as e:
                print("Could not initalize ECU, trying again in 3 seconds")
                print(e)
                time.sleep(3)

    def close(self):
        """
        Close the serial connection.
        """
        self.ser.close()




# print("---")
# print("Packet Read:")
# print(f"Returned Number of Bytes: {len(response)}")
# print(f"Expected Returned Number of Bytes: {responseLength}")
# print(" ".join(hex(n) for n in response))
# print(f"Start Byte: {hex(response[0])}")
# print(f"Destination Byte: {hex(response[1])}")
# print(f"Source Byte: {hex(response[2])}")
# print(f"Data Size Byte: {hex(response[3])}")
# print(f"Data Size Int: {response[3]}")
# datalen = int(response[3])
# print(f"Data Bytes Hex: {" ".join(hex(n) for n in response[4:4 + datalen])}")
# print(f"Data Bytes Int: {list(response[4:4 + datalen])}")
# print(f"Calculated Checksum: {hex(self.calculate_checksum(response[:4 + datalen]))}")
# print(f"Returned Checksum: {response[4 + datalen: 5 + datalen].hex()}")
# DEBUG