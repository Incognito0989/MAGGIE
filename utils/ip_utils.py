import time
import ipaddress
import subprocess
import platform
from utils.api_utils import *
from utils.switch_utils import *

def ip_range(start_ip, end_ip):
    start = ipaddress.ip_address(start_ip)
    end = ipaddress.ip_address(end_ip)
    for ip in range(int(start), int(end) + 1):
        yield ipaddress.ip_address(ip)


# def is_ip_reachable(ip, timeout=2, attempts=10):
#     # Determine the command to use based on the operating system
#     param = "-n" if platform.system().lower() == "windows" else "-c"
#     command = ["ping", param, "10", str(ip)]
    
#     try:
#         # Run the ping command with the specified timeout
#         subprocess.check_call(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=timeout)
#         return True  # IP is reachable
#     except subprocess.TimeoutExpired:
#         print(f"IP {ip} is not reachable (timed out). Skipping")
#         return False  # Timeout occurred
#     except subprocess.CalledProcessError:
#         print(f"IP {ip} is not reachable (ping failed). Skipping")
#         return False  # Ping failed

from netmiko import ConnectHandler

def force_arp_update(switch_ip, username, password, target_ip):
    print("Forcing arp update on switch")
    device = {
        "device_type": "cisco_ios",  # Change based on switch vendor (e.g., "hp_procurve", "juniper", etc.)
        "host": switch_ip,
        "username": username,
        "password": password,
        "fast_cli": False,
    }

    try:
        # Connect to the switch
        net_connect = ConnectHandler(**device)
        
        # Run ping command
        output = net_connect.send_command(f"ping {target_ip}")
        
        print(output)  # Print the result

        # Close connection
        net_connect.disconnect()
    except Exception as e:
        print(f"SSH Error: {e}")

def is_ip_reachable(ip, duration=60):
    """
    Check if an IP is reachable for a specified duration.

    :param ip: IP address to check
    :param duration: Total time (in seconds) to keep checking
    :return: True if the device becomes reachable, False otherwise
    """
    param = "-n" if platform.system().lower() == "windows" else "-c"
    start_time = time.time()

    while time.time() - start_time < duration:
        command = ["ping", param, "1", str(ip)]
        try:
            clear_arp_cache(switch_ip, switch_username, switch_password, switch_enable_password)
            force_arp_update(switch_ip, switch_username, switch_password, target_ip=ip)
            subprocess.check_call(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True  # Device is reachable
        except subprocess.CalledProcessError:
            time.sleep(1)  # Wait before retrying
    
    return False  # Timeout reached without success