from pysnmp.hlapi import *

# physical port is 47
management_port = 48



#in progress helper function
def get_admin_status(switch_ip, port_index, community):
    ifAdminStatus_oid_base = '1.3.6.1.2.1.2.2.1.7' # Admin status
    oid = f"{ifAdminStatus_oid_base}.{port_index}"
    # Get Admin Status
    errorIndication, errorStatus, errorIndex, varBinds = nextCmd(
        SnmpEngine(),
        CommunityData(community),
        UdpTransportTarget((switch_ip, 161)),
        ContextData(),
        ObjectType(ObjectIdentity(oid)),
        lexicographicMode=False
    )
    if errorIndication or errorStatus:
        print(f"Error: {errorIndication or errorStatus}")
        return []
    for varBind in varBinds:
        oid, value = varBind
        index = oid.prettyPrint().split('.')[-1]
        if index in ports:
            ports[index]['admin_status'] = int(value)  # 1=up, 2=down, 3=testing

#in progress not implemented
def get_all_admin_status(switch_ip, community='public'):
    ports = get_port_list(switch_ip)
    for port in ports:
        print(get_admin_status(switch_ip, port['index'], community))

def get_all_port_status(switch_ip, community='public'):
    """
    Get the status (admin and operational) of all ports on the switch.

    Args:
        switch_ip (str): IP address of the switch.
        community (str): SNMP community string (default: 'public').

    Returns:
        list: A list of dictionaries with port index, name, admin status, and operational status.
    """
    # OIDs for ifDescr, ifAdminStatus, and ifOperStatus
    ifDescr_oid = '1.3.6.1.2.1.2.2.1.2'      # Port name
    ifAdminStatus_oid = '1.3.6.1.2.1.2.2.1.7' # Admin status
    ifOperStatus_oid = '1.3.6.1.2.1.2.2.1.8'  # Operational status
    
    # SNMP Walk for ifDescr (Port names)
    ports = {}
    for (errorIndication, errorStatus, errorIndex, varBinds) in nextCmd(
        SnmpEngine(),
        CommunityData(community),
        UdpTransportTarget((switch_ip, 161)),
        ContextData(),
        ObjectType(ObjectIdentity(ifDescr_oid)),
        lexicographicMode=False
    ):
        if errorIndication or errorStatus:
            print(f"Error: {errorIndication or errorStatus}")
            return []
        for varBind in varBinds:
            oid, value = varBind
            index = oid.prettyPrint().split('.')[-1]
            ports[index] = {'name': value.prettyPrint()}
    
    # Get Admin Status
    for (errorIndication, errorStatus, errorIndex, varBinds) in nextCmd(
        SnmpEngine(),
        CommunityData(community),
        UdpTransportTarget((switch_ip, 161)),
        ContextData(),
        ObjectType(ObjectIdentity(ifAdminStatus_oid)),
        lexicographicMode=False
    ):
        if errorIndication or errorStatus:
            print(f"Error: {errorIndication or errorStatus}")
            return []
        for varBind in varBinds:
            oid, value = varBind
            index = oid.prettyPrint().split('.')[-1]
            if index in ports:
                ports[index]['admin_status'] = int(value)  # 1=up, 2=down, 3=testing
    
    # Get Operational Status
    for (errorIndication, errorStatus, errorIndex, varBinds) in nextCmd(
        SnmpEngine(),
        CommunityData(community),
        UdpTransportTarget((switch_ip, 161)),
        ContextData(),
        ObjectType(ObjectIdentity(ifOperStatus_oid)),
        lexicographicMode=False
    ):
        if errorIndication or errorStatus:
            print(f"Error: {errorIndication or errorStatus}")
            return []
        for varBind in varBinds:
            oid, value = varBind
            index = oid.prettyPrint().split('.')[-1]
            if index in ports:
                ports[index]['oper_status'] = int(value)  # 1=up, 2=down, etc.
    
    # Format output
    result = []
    for index, port in ports.items():
        result.append({
            'port': index,
            'name': port['name'],
            'admin_status': port['admin_status'],
            'oper_status': port['oper_status']
        })
    
    return result


def get_active_ports(switch_ip, port_list=None, community='public'):
    """
    Returns a list of ports that have an operational status of 'up'.

    Args:
        switch_ip (str): IP address of the switch
        port_list (list): List of port numbers (as integers)
        community (str): SNMP community string (default: public)

    Returns:
        list: List of ports with operational status 'up'
    """
    #get port list if not provided
    if(port_list is None):
        port_list = get_port_list(switch_ip)

    active_ports = []
    oper_status_oid_prefix = "1.3.6.1.2.1.2.2.1.8"  # OID prefix for ifOperStatus

    for port in port_list:
        oid = f"{oper_status_oid_prefix}.{port}"
        error_indication, error_status, error_index, var_binds = next(
            getCmd(
                SnmpEngine(),
                CommunityData(community),
                UdpTransportTarget((switch_ip, 161)),
                ContextData(),
                ObjectType(ObjectIdentity(oid))
            )
        )

        if error_indication:
            print(f"Error for port {port}: {error_indication}")
        elif error_status:
            print(f"Error for port {port}: {error_status.prettyPrint()}")
        else:
            for var_bind in var_binds:
                # ifOperStatus: 1 (up), 2 (down), etc.
                status = int(var_bind[1])
                if status == 1:  # Operationally 'up'
                    active_ports.append(port)

    return active_ports




def get_all_physical_ports(switch_ip, community='public'):
    """
    Retrieve all ports (interfaces) from the switch using SNMP.
    
    Args:
        switch_ip (str): IP address of the switch.
        community (str): SNMP community string (default: 'public').

    Returns:
        list: A list of tuples where each tuple contains (interface_index, interface_name).
    """
    # OID for ifDescr (interface descriptions)
    ifDescr_oid = '1.3.6.1.2.1.2.2.1.2'
    ports = []

    for (errorIndication, errorStatus, errorIndex, varBinds) in nextCmd(
        SnmpEngine(),
        CommunityData(community),
        UdpTransportTarget((switch_ip, 161)),
        ContextData(),
        ObjectType(ObjectIdentity(ifDescr_oid)),
        lexicographicMode=False
    ):
        if errorIndication:
            print(f"Error: {errorIndication}")
            break
        elif errorStatus:
            print(f"Error: {errorStatus.prettyPrint()}")
            break
        else:
            for varBind in varBinds:
                oid, value = varBind
                index = str(oid).split('.')[-1]
                name = str(value)

                # Filter only physical ports
                if 'Ethernet1/' in name:
                    ports.append((index, name))

    return ports

def get_connected_ports_and_ips(switch_ip, community='public'):
    """
    Get connected ports and their associated IP addresses by combining the MAC, ARP, and port status information.
    :param switch_ip: IP address of the switch.
    :param community: SNMP community string.
    :return: List of dictionaries with port and IP mappings.
    """
    port_descriptions = get_port_descriptions(switch_ip, community)
    port_status = get_port_status(switch_ip, community)
    mac_addresses = get_mac_addresses(switch_ip, community)
    arp_table = get_arp_table(switch_ip, community)
    
    connected_ports = {}
    
    # Step 1: Identify 'up' ports and associate them with their descriptions
    for port_index, status in port_status.items():
        if status == 'up':
            port_desc = port_descriptions.get(f'1.3.6.1.2.1.2.2.1.2.{port_index}', f'Port-{port_index}')
            connected_ports[port_index] = {'port': port_desc, 'macs': [], 'ips': []}
    
    # Step 2: Add MAC addresses to connected ports
    for port_index, mac_list in mac_addresses.items():
        if port_index in connected_ports:
            connected_ports[port_index]['macs'].extend(mac_list)
    
    # Step 3: Map MAC addresses to IP addresses
    for port_index, details in connected_ports.items():
        for mac in details['macs']:
            ip = arp_table.get(mac)
            if ip:
                details['ips'].append(ip)
    
    # Format the results for output
    results = [{'port': details['port'], 'ips': details['ips']} for details in connected_ports.values()]
    
    return results


### HELPER
from pysnmp.hlapi import *

def is_port_operational(switch_ip, port_index, community='public'):
    """
    Check if a specific port is operational using SNMP.
    
    Args:
        switch_ip (str): IP address of the switch.
        port_index (int): Index of the port to check.
        community (str): SNMP community string (default: 'public').

    Returns:
        bool: True if the port is operational (up), False otherwise.
    """
    # OID base for ifOperStatus
    oid = f'1.3.6.1.2.1.2.2.1.8.{port_index}'  # Replace {port_index} dynamically

    # Perform SNMP GET
    errorIndication, errorStatus, errorIndex, varBinds = next(
        getCmd(
            SnmpEngine(),
            CommunityData(community),
            UdpTransportTarget((switch_ip, 161)),
            ContextData(),
            ObjectType(ObjectIdentity(oid))
        )
    )

    # Handle SNMP errors
    if errorIndication:
        print(f"Error: {errorIndication}")
        return False
    elif errorStatus:
        print(f"Error: {errorStatus.prettyPrint()}")
        return False

    # Extract the status value
    for varBind in varBinds:
        status = int(varBind[1])  # SNMP response value (integer)

    # Return True if operational (1 = up), otherwise False
    return status == 1


def is_management(port_index):
    """
    Compares if a port is the management port

    returns:
    True if the port is the management port
    """
    return (str(port_index) == str(management_port))

def get_port_list(switch_ip):
    """
    Get the list of ports other than management.
    We exclude management port to ensure dont lose connection to switch.
    
    Args:
    switch_ip (str): IP address of the switch.

    Returns:
    list: A list of dictionaries with port index ie. ['2', '3', '4', '5']
    """
    ports = get_all_physical_ports(switch_ip)
    return [item[0] for item in ports if not is_management(item[0])]



### UPDATE PORT FUNCTIONS
def set_port(switch_ip, port_index, status=1, community='private'):
    """
    Enable a port on a switch via SNMP.

    :param switch_ip: The IP address of the switch.
    :param port_number: The port number to enable (e.g., 1, 2, 3...).
    :param community: SNMP community string (default is 'public').
    """
    # OID for ifAdminStatus (1.3.6.1.2.1.2.2.1.7)
    ifAdminStatus_oid_base = '1.3.6.1.2.1.2.2.1.7'

    # Setting to 1 enables the port (down = 2, testing = 3)
    oid = f"{ifAdminStatus_oid_base}.{port_index}"
    # set_port(switch_ip, port_index, 1)
    errorIndication, errorStatus, errorIndex, varBinds = next(
        setCmd(
            SnmpEngine(),
            CommunityData(community, mpModel=0),  # Ensure write community
            UdpTransportTarget((switch_ip, 161)),
            ContextData(),
            ObjectType(ObjectIdentity(oid), Integer(status))  # Set admin status to 2 (down)
        )
    )
    if errorIndication:
        print(f"Error turning off port {port_index}: {errorIndication}")
    elif errorStatus:
        print(f"Error on port {port_index}: {errorStatus.prettyPrint()}")
    # else:
    #     print(f"Successfully set port {port_index} status to {status}")

def update_all_ports(switch_ip, status=1, community='private'):
    """
    Change status of all ports on the switch

    :param switch_ip: The IP address of the switch.
    :param port_number: The port number to enable (e.g., 1, 2, 3...).
        1 = On
        2 = Off
    :param community: SNMP community string (default is 'public').
    """
    # Get the list of all ports
    ports = get_port_list(switch_ip)
    failed_ports = []

    for port in ports:
        if str(port) == str(management_port):
            print("Skipping moddification to management port: " + port)
            continue
        try:
            set_port(switch_ip, port, status, community)  # Attempt to set port
        except Exception as e:
            failed_ports += port
            print(f"Failed to modify port {port}: {e}")
        
    # Final message after the loop
    if failed_ports:
        print("The following ports failed to be modified:", failed_ports)
    else:
        print("All ports were successfully modified.")




### GETTER SNMP WALKS ALL PORTS
def snmp_walk(oids, switch_ip, community='public'):
    """
    Perform an SNMP walk for multiple OIDs and return the results as a dictionary.
    :param oids: List of OIDs to query.
    :param switch_ip: IP address of the switch.
    :param community: SNMP community string.
    :return: Dictionary of OIDs and their values.
    """
    result = {}
    
    for oid in oids:
        for errorIndication, errorStatus, errorIndex, varBinds in nextCmd(
            SnmpEngine(),
            CommunityData(community),
            UdpTransportTarget((switch_ip, 161)),
            ContextData(),
            ObjectType(ObjectIdentity(oid)),
            lexicographicMode=False
        ):
            if errorIndication or errorStatus:
                print(errorIndication or errorStatus)
                break
            for varBind in varBinds:
                result[str(varBind[0])] = varBind[1].prettyPrint()

    return result

def get_port_descriptions(switch_ip, community='public'):
    """
    Get port descriptions (interface names) from the switch.
    :param switch_ip: IP address of the switch.
    :param community: SNMP community string.
    :return: Dictionary with port index as key and port description as value.
    """
    if_descr_oid = '1.3.6.1.2.1.2.2.1.2'  # OID for interface descriptions
    return snmp_walk([if_descr_oid], switch_ip, community)

def get_port_status(switch_ip, community='public'):
    """
    Get the status of each port (up or down).
    :param switch_ip: IP address of the switch.
    :param community: SNMP community string.
    :return: Dictionary with port index as key and status as value.
    """
    if_status_oid = '1.3.6.1.2.1.2.2.1.8'  # OID for interface status
    status_dict = snmp_walk([if_status_oid], switch_ip, community)
    
    # Convert status from SNMP values: 1=up, 2=down
    return {k.split('.')[-1]: 'up' if int(v) == 1 else 'down' for k, v in status_dict.items()}

def get_mac_addresses(switch_ip, community='public'):
    """
    Get MAC addresses associated with each port.
    :param switch_ip: IP address of the switch.
    :param community: SNMP community string.
    :return: Dictionary with port index as key and list of MAC addresses as value.
    """
    mac_table_oid = '1.3.6.1.2.1.17.4.3.1.2'  # OID for MAC address table
    result = snmp_walk([mac_table_oid], switch_ip, community)
    
    mac_dict = {}
    for port_index, mac_raw in result.items():
        mac = ':'.join([f'{int(x):02x}' for x in mac_raw.split('.')[-6:]])
        mac_dict.setdefault(port_index.split('.')[-1], []).append(mac)

    return mac_dict

def get_arp_table(switch_ip, community='public'):
    """
    Get the ARP table, mapping IP addresses to MAC addresses.
    :param switch_ip: IP address of the switch.
    :param community: SNMP community string.
    :return: Dictionary with MAC addresses as keys and IP addresses as values.
    """
    arp_table_oid = '1.3.6.1.2.1.4.22.1.2'  # OID for ARP table
    result = snmp_walk([arp_table_oid], switch_ip, community)
    
    arp_dict = {}
    for ip_raw, mac_raw in result.items():
        ip = '.'.join(ip_raw.split('.')[-4:])
        if mac_raw.startswith('0x'):
            mac = ':'.join(mac_raw[i:i + 2] for i in range(2, len(mac_raw), 2))
        else:
            mac = ':'.join([f'{int(x):02x}' for x in mac_raw.split('.')])
        
        arp_dict[mac] = ip
    
    return arp_dict






# Example usage
switch_ip = '10.4.11.240'
# community = 'public'

# update_all_ports(switch_ip, 1)
# # ports = get_port_status(switch_ip, community)
# # print(ports)
# # print(get_all_physical_ports(switch_ip))
# # print(get_port_list(switch_ip))
# # update_all_ports(switch_ip, 1)
# # set_port(switch_ip, 1, 2)
# # update_status_all_ports(switch_ip, 2)
# # set_port(switch_ip, 51, 2)
# # ports = get_all_physical_ports(switch_ip, community)
# # # get_all_status(switch_ip)
# # # print(get_port_list(switch_ip))
# # # ports = snmp_walk(["1.3.6.1.2.1.2.2.1.7"], switch_ip)
# # # # ports = get_port_descriptions(switch_ip)
# ports = get_all_port_status(switch_ip)
# for entry in ports:
#     print(entry)
# set_port(switch_ip, 14, 1)
# print(is_port_operational(switch_ip, 14))