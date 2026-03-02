import xml.etree.ElementTree as ET
from typing import Dict, Any, Optional, Tuple

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

# Example usage
if __name__ == "__main__":
    # Parse the XML file
    param_lookup = parse_ecu_parameters("logger.xml")
    
    # Get information for a specific parameter by byte/bit index
    info = get_parameter_info(param_lookup, 8, 7)
    if info:
        print("Parameter by index:", info["id"], info["name"], info["addresses"], info["address length"], info["conversions"])
    
    # Get information for a specific parameter by ID
    info_by_id = get_parameter_by_id(param_lookup, "P1")
    if info_by_id:
        print("Parameter by ID:", info_by_id["id"], info_by_id["name"], info_by_id["addresses"], info_by_id["address length"], info_by_id["conversions"])
