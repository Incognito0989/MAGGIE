import ipaddress
import subprocess
import platform
from utils.api_utils import *

def process_service_for_ip(service_type, ip, service_dir):
    service_functions = {
        "decode": post_decode_service,
        "transcode": post_transcode_service,
        "descramble": post_descramble_service
    }
    
    if service_type in service_functions:
        service_functions[service_type](ip, service_dir)

def ip_range(start_ip, end_ip):
    start = ipaddress.ip_address(start_ip)
    end = ipaddress.ip_address(end_ip)
    for ip in range(int(start), int(end) + 1):
        yield ipaddress.ip_address(ip)


def is_ip_reachable(ip, timeout=2):
    # Determine the command to use based on the operating system
    param = "-n" if platform.system().lower() == "windows" else "-c"
    command = ["ping", param, "1", str(ip)]
    
    try:
        # Run the ping command with the specified timeout
        subprocess.check_call(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=timeout)
        return True  # IP is reachable
    except subprocess.TimeoutExpired:
        print(f"IP {ip} is not reachable (timed out). Skipping")
        return False  # Timeout occurred
    except subprocess.CalledProcessError:
        print(f"IP {ip} is not reachable (ping failed). Skipping")
        return False  # Ping failed