import serial
import struct
import time
import xml.etree.ElementTree as ET
from typing import Dict, Any, Optional, Tuple

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
                # print(f"{' '.join(hex(n) for n in response)}")
                print(f"ECU Initalized, ECU ID is: {' '.join(hex(n) for n in response[8:13])}")
                initialized = True
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

    def parse_ecu_parameters(xml_file: str) -> Dict[Tuple[int, int], Dict[str, Any]]:
        """
        Parse ECU parameters from an XML file and return a lookup dictionary.
        
        Args:
            xml_file: Path to the XML file containing ECU parameter definitions
            
        Returns:
            Dictionary mapping (byte_index, bit_index) tuples to parameter information
        """
        tree = ET.parse(xml_file)
        root = tree.getroot()
        
        param_lookup = {}
        
        for param in root.findall("protocols/protocol/parameters/parameter"):
            byte_index = param.get("ecubyteindex")
            bit_index = param.get("ecubit")
            
            if byte_index is not None and bit_index is not None:
                key = (int(byte_index), int(bit_index))
                address_el = param.find("address")
                
                # Handle address and length
                addresses = []
                if address_el is not None:
                    address = address_el.text
                    length = address_el.get("length")
                    if address is not None:
                        addresses.append(address)
                        if length is not None:
                            # Convert hex address to integer, add 1, then convert back to hex
                            try:
                                addr_int = int(address, 16)
                                next_addr_int = addr_int + 1
                                next_address = f"0x{next_addr_int:06X}"
                                addresses.append(next_address)
                            except ValueError:
                                pass  # Keep addresses as single item if conversion fails
                
                param_lookup[key] = {
                    "id": param.get("id"),
                    "name": param.get("name"),
                    "desc": param.get("desc"),
                    "addresses": addresses,
                    "address length": len(addresses),
                    "conversions": param.find("conversions")
                }
                
                conversions = param.find("conversions")
                if conversions is not None:
                    for conv in conversions.findall("conversion"):
                        param_lookup[key]["conversions"] = {
                            "units": conv.get("units"),
                            "expr": conv.get("expr"),
                            "format": conv.get("format"),
                            "gauge_min": conv.get("gauge_min"),
                            "gauge_max": conv.get("gauge_max"),
                            "gauge_step": conv.get("gauge_step"),
                        }
        
        return param_lookup

    def get_parameter_info(param_lookup: Dict[Tuple[int, int], Dict[str, Any]], byte_index: int, bit_index: int) -> Optional[Dict[str, Any]]:
        """
        Get parameter information for a specific byte and bit index.
        
        Args:
            param_lookup: Dictionary of parameter information
            byte_index: Byte index to look up
            bit_index: Bit index to look up
            
        Returns:
            Dictionary containing parameter information if found, None otherwise
        """
        return param_lookup.get((byte_index, bit_index))

    def get_parameter_by_id(param_lookup: Dict[Tuple[int, int], Dict[str, Any]], param_id: str) -> Optional[Dict[str, Any]]:
        """
        Get parameter information by its ID.
        
        Args:
            param_lookup: Dictionary of parameter information
            param_id: ID of the parameter to look up
            
        Returns:
            Dictionary containing parameter information if found, None otherwise
        """
        for param_info in param_lookup.values():
            if param_info["id"] == param_id:
                return param_info
        return None