import serial
import struct
import time

class PySSM2:
    def __init__(self, port, baudrate=4800, timeout=1):
        """
        Initialize the SSM2Protocol class with the default serial communication settings.
        """
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.source = 0xF0  # Default source address (Diagnostic Tool)
        self.destination = 0x10  # Destination address (Subaru ECU)
        self.ser = serial.Serial(port, baudrate, timeout=timeout)  # Initialize serial connection

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
        return response[len(packet):]
    
    def receive_packet(self, responseLength):
        response = self.ser.read(responseLength)
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
        if not response:
            raise TimeoutError("No response received from ECU.")
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
        data = [0xA8, 0x01]  # Byte for reading single address + Pad Byte
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

    def ecu_init(self):
        """
        Send an ECU initialization request and return the response.
        """
        data = [0xBF]
        initialized = False
        self.ser.flush()
        while not initialized:
            try:
                response = self.send_packet(data)
                # print(f"{' '.join(hex(n) for n in response)}")
                print(response)
                # print(f"ECU Initalized, ECU ID is: {' '.join(hex(n) for n in response[8:13])}")
                initialized = True
                self.ser.timeout = 0.07 # I found this is a good timeout
                return response
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