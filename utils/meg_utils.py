from netmiko import ConnectHandler, file_transfer
from settings import *
import re
import requests
import json
import time
import ipaddress
import subprocess
import platform
from utils.switch_utils import *
from netmiko import ConnectHandler
import os
import pexpect
from time import sleep

# ## GLOBAL VARIABLES
# management_port = 49            #this is physical port 48
# switch_ip = "10.4.11.240"
# switch_username = "netadmin"  # Replace with your username
# switch_password = "Syn@123!!"  # Replace with your SSH login password
# switch_enable_password = "Syna1234"  # Replace with your enable password

# meg_ip = "192.168.2.20"
# meg_username="root"
# meg_password="$ynamedia"
# meg_rest_username="maggie"
# meg_rest_password="maggie"

# port_exclusions = [management_port]
# ## port range that is being used is  2 ... 49
class MegManager:
    def __init__(self, payload, 
                 processing_type, 
                 service_dir, 
                 ip=meg_ip, 
                 rest_username=meg_rest_username, 
                 rest_password=meg_rest_password,
                 username=meg_username,
                 password=meg_password,
                 pcie_port='00000000-0000-0000-0000-000000000002'):
        self.TOKEN = None
        self.ip = ip
        self.processing_type = processing_type
        self.rest_username = rest_username
        self.rest_password = rest_password
        self.username = username
        self.password = password
        self.service_dir = service_dir
        self.payload = payload
        self.file_name = os.path.basename(self.payload)
        self.pcie_port = pcie_port
        self.device = {
            "device_type": "linux",
            "host": self.ip,
            "username": "root",
            "password": "password",
            "session_log": "netmiko_debug.log",  # Logs session for debugging
        }
        self.ssh_command = f"ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o LogLevel=ERROR {self.device["username"]}@{self.device["host"]}"


    def configure(self):
        print("--- Meg Configuration Beginning ---")
        self.is_ip_reachable(duration=60)
        self.change_expired_password()
        self.reset_password_ssh()
        self.confirm_rest_service()
        self.make_rest_user()
        self.post_auth()
        self.put_set_output_port()
        self.process_service_for_ip()
        self.cleanup()


    def change_expired_password(self):
        """Handle forced password change over SSH using pexpect and show terminal output."""

        # Start the SSH session
        child = pexpect.spawn(self.ssh_command, encoding='utf-8')

        # Enable logging to stdout (prints all interactions)
        # child.logfile = sys.stdout  # Show output in the terminal
        print("Starting SSH session...")

        # Handle SSH key verification prompt
        index = child.expect([
            'Are you sure you want to continue connecting (yes/no/[fingerprint])?',
            'password: ',
            pexpect.TIMEOUT
        ], timeout=15)

        if index == 0:
            print("SSH key verification required, sending 'yes'...")
            child.sendline("yes")
            child.expect('password: ', timeout=15)
            child.expect('')
            child.expect('password: ', timeout=15)
        print("Password prompt received.")
        child.sendline(self.device["password"])
        print(f"Sent password: {self.device["password"]}")

        # Handle forced password change prompt
        child.expect("You are required to change your password immediately", timeout=15)
        print("Password change required...")

        child.expect('password: ', timeout=15)
        print("Password prompt received again for confirmation.")
        child.sendline(self.device["password"])
        print(f"Sent current password again: {self.device["password"]}")

        # See what response comes next
        child.expect(['New password: ', 'The password fails the dictionary check', pexpect.TIMEOUT], timeout=30)
        print(f"Received response: {child.after}")  # Print the exact response

        if 'The password fails the dictionary check' in child.after:
            print("Password failed dictionary check, retyping...")
            child.sendline(self.password)

        # Send new password
        child.expect('New password: ', timeout=30)
        print("New password prompt received.")
        child.sendline(self.password)
        print(f"Sent new password: {self.password}")

        # Wait for the retype password prompt and send again
        child.expect('Retype new password: ', timeout=30)
        print("Retype new password prompt received.")
        child.sendline(self.password)
        print(f"Retyped new password: {self.password}")

        # Wait for success message
        child.expect(['successfully', pexpect.TIMEOUT], timeout=30)
        print(f"Final response: {child.after}")  # Print final confirmation or timeout

        child.close()


    def reset_password_ssh(self):
        """Log in again with temp password and reset to original password."""

        child = pexpect.spawn(self.ssh_command, encoding='utf-8')
        # child.logfile = sys.stdout  # Print interactions

        child.expect('password: ', timeout=15)
        print("Logging in again to reset password.")
        child.sendline(self.password)

        # Send pub id to authkeys
        print("Adding Maggie's public key")
        child.expect(']#')
        child.sendline(f'echo "{pub_key}" >> ~/.ssh/authorized_keys')

        # Run passwd command
        child.expect(f'{self.device["username"]}@', timeout=15)
        child.sendline('passwd')

        # Expect password prompts
        child.expect('New password: ', timeout=15)
        child.sendline(self.device["password"])
        child.expect('Retype new password: ', timeout=15)
        child.sendline(self.device["password"])

        # Confirm success
        child.expect(['password updated successfully', pexpect.TIMEOUT], timeout=15)
        print(f"Password reset response: {child.after}")

        child.close()
        print("Password reset completed.")


    def cleanup(self):
        print("Cleaning up meg to fresh look")
        print(f"Connecting to device: {self.ip}")
        print(self.device)
        with ConnectHandler(**self.device) as ssh:
            print("Connected successfully!")

            # print("Removing all users")
            # output = ssh.send_command_timing("meg-configure user --remove-all-users")
            # print(output)

            print("Restarting MEG service")
            output = ssh.send_command_timing("meg-configure service --restart")
            print(output)

            print("Cleanup OS user/history and keys")
            output = ssh.send_command_timing("shred -u /root/.ssh/authorized_keys && chage -d 0 root && history -c")


    def clean(self):
        child = pexpect.spawn(self.ssh_command, encoding='utf-8')
        try:
            print("Connected!")
            print("Cleaning up meg to fresh look")

            print("Removing all users")
            child.expect(']#')
            child.sendline("meg-configure user --remove-all-users")

            print("Restarting MEG service")
            child.expect(']#')
            child.sendline("meg-configure service --restart")

            print("Cleanup OS user/history and keys")
            child.expect(']#')
            child.sendline("shred -u /root/.ssh/authorized_keys && chage -d 0 root && history -c")

            print("Cleanup complete")

        except Exception as e:
            print(f"Error: {e}")


    def confirm_rest_access(self, attempt=0, retries=3, delay=5):
        print("Confirming REST")
        child = pexpect.spawn(self.ssh_command, encoding='utf-8')
        try:
            print("Connected")
            print("Confirming rest service running")
            child.expect(']#')
            child.sendline('meg-configure service --enable-rest')
            print("Rest enabled!")

            print("Removing rest user")
            child.expect(']#')
            child.sendline(f"meg-configure user --remove {self.rest_username}")
            print("Users removed")

            print("Making rest user")
            child.expect(']#')
            child.sendline(f"meg-configure user --add {self.rest_username} --ignore-passphrase-policy  --passphrase {self.rest_password} --gui-admin --rest-user")
            print(f"User {self.rest_username} created successfully!")

        except Exception as e:
            print(f"Error: {e}")
            if attempt < retries:
                print(f"Retrying in {delay} seconds...")
                time.sleep(delay)  # Wait before retrying
                self.confirm_rest_access(retries, delay, attempt + 1)  # Recursive call with incremented attempt
            else:
                print("Max retries reached. REST configuration failed.")
                raise RuntimeError("Max retries reached. REST configuration failed.")


    def confirm_rest_service(self, attempt=0, retries=3, delay=5):
        try:
            print("Confirm rest service running")
            print(f"Connecting to device: {self.ip}")
            print(self.device)
            with ConnectHandler(**self.device) as ssh:
                print("Connected successfully!")

                # Get current services
                print("Confirming rest is enabled...")
                output = ssh.send_command_timing(" meg-configure service --enable-rest")
                print(output)

        except Exception as e:
            print(f"Error: {e}")
            if attempt < retries:
                print(f"Retrying in {delay} seconds...")
                time.sleep(delay)  # Wait before retrying
                self.confirm_rest_service(retries=retries, delay=delay, attempt=(attempt + 1))  # Recursive call with incremented attempt
            else:
                print("Max retries reached. REST service configuration failed.")
                raise RuntimeError("Max retries reached. REST service configuration failed.")


    def make_rest_user(self, attempt=0, retries=3, delay=5):
        try:
            print("Create rest user")
            print(f"Connecting to device: {self.ip}")
            print(self.device)
            with ConnectHandler(**self.device) as ssh:
                print("Connected successfully!")

                print("Cleaning previous users...")
                print(ssh.send_command_timing(f"meg-configure user --remove {self.rest_username}"))
                
                print("Making new rest user...")
                print(ssh.send_command_timing(f"meg-configure user --add {self.rest_username} --ignore-passphrase-policy  --passphrase {self.rest_password} --gui-admin --rest-user"))

                print(f"User {self.rest_username} created successfully!")

        except Exception as e:
            print(f"Error: {e}")
            if attempt < retries:
                print(f"Retrying in {delay} seconds...")
                time.sleep(delay)  # Wait before retrying
                self.make_rest_user(retries=retries, delay=delay, attempt=(attempt + 1))  # Recursive call with incremented attempt
            else:
                print("Max retries reached. REST user configuration failed.")
                raise RuntimeError("Max retries reached. REST user configuration failed.")


    def put(self, url, body):
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': self.TOKEN
        }

        response = requests.put(url, headers=headers, json=body, verify=False)
        response.raise_for_status()  # Raises an error for 4xx/5xx responses

        print(response.text)

        if 'errors' in response.text.lower():  # Case-insensitive check
            raise RuntimeError(f"Error in response: {response.text}")
        
    
    def get(self, url):
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': self.TOKEN
        }

        response = requests.get(url, headers=headers, verify=False)
        response.raise_for_status()  # Raises an error for 4xx/5xx responses

        print(response.text)

        if 'errors' in response.text.lower():  # Case-insensitive check
            raise RuntimeError(f"Error in response: {response.text}")
        return response


    def post(self, url):
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': self.TOKEN
        }

        with open(self.payload, "r") as file:
            self.payload = json.load(file)

        response = requests.post(url, headers=headers, json=self.payload, verify=False)
        response.raise_for_status()  # Raises an error for 4xx/5xx responses

        print(response.text)

        if 'errors' in response.text.lower():  # Case-insensitive check
            raise RuntimeError(f"Error in response: {response.text}")


    def process_service_for_ip(self):
        service_functions = {
            "Decode": self.post_decode_service,
            "Transcode": self.post_transcode_service,
            "Descramble": self.post_descramble_service,
            "ServiceRoute": self.post_service_route,
            "TSRoute": self.post_ts_route
        }
        
        if self.processing_type in service_functions:
            return service_functions[self.processing_type]()


    def post_auth(self):
        print(f"Getting authorization for {self.ip}")
        url = f"https://{self.ip}:8443/api/authenticate"

        cred = {
            "login": self.rest_username,
            "password": self.rest_password
        }
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }

        # Send the authentication request
        response = requests.post(url, headers=headers, json=cred, verify=False)
        
        # Raise an error for bad HTTP status codes (4xx, 5xx)
        response.raise_for_status()

        # Parse JSON response
        response_data = response.json()

        # Extract the token
        self.TOKEN = response_data.get('token')

        if self.TOKEN:
            print(f"SUCCESS, got token: {self.TOKEN}")
            return 'success'
        else:
            print(f"Error: Token missing in response from {self.ip}")
            raise RuntimeError(f"Error: Token missing in response from {self.ip}")
        

    def post_decode_service(self):
        print(f"Posting decode service to {self.ip} with payload: {self.file_name}")
        url = f"https://{self.ip}:8443/api/v2/DecodeServices?results=false"
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': self.TOKEN
        }

        print('...HEADERS...')
        print(headers)

        # Load payload from file
        with open(self.payload, "r") as file:
            self.payload = json.load(file)

        print(self.payload)

        # Send HTTP POST request
        response = requests.post(url, headers=headers, json=self.payload, verify=False)

        # Raise an error for bad HTTP status codes (4xx, 5xx)
        response.raise_for_status()

        print(f"Response [{response.status_code}]: {response.text}")


    def put_set_output_port(self):
        print(f"POST: Setting port of device")

        # Read JSON file
        with open(self.payload, "r") as file:
            data = json.load(file)

        output_type, output_interface = None, None

        if self.processing_type in ["Transcode"]:
            temp_data = data.get("outputs", [{}])[0].get("outputService", {}).get("outputTS", {})
            output_type = temp_data.get("outputType", "")
            output_interface = temp_data.get("interface", "")

        elif self.processing_type in ["Decode"]:
            temp_data = data.get("outputs", [{}])[0]
            output_type = temp_data.get("outputType", "")
            output_interface = temp_data.get("interface", "")

        elif self.processing_type in ["ServiceRoute"]:
            temp_data = data.get("outputService", {}).get("outputTS", {})
            output_type = temp_data.get("outputType", "")
            output_interface = temp_data.get("interface", "")

        elif self.processing_type in ["TSRoute"]:
            temp_data = data.get("outputLTTS", {})
            output_type = temp_data.get("outputType", "")
            output_interface = temp_data.get("asiSettings", {}).get("interface", "")

        if not output_type:
            raise ValueError("[ERROR] No valid outputType found in any path... json file may have wrong structure")

        # Determine physicalType value
        physical_type = output_type if output_type in ["SDI", "ASI"] else None

        if physical_type is None or output_interface == "":
            print("[INFO] physical output type is not to be changed")
            return
        
        if output_interface == None:
            output_interface = "ASI_P1" if physical_type == "ASI" else "SDI1"
            print(f"[INFO] Output interface being set to default value {output_interface}")
        
        # Print the result of the conditional check
        print(f"Setting physicalType to: {physical_type} with interface name: {output_interface}")

        url = f"https://{self.ip}:8443/api/v2/AppSettings/Node/Configuration/PCI/{self.pcie_port}"
        payload = json.dumps({
            "ports": [
                {
                    "userName": output_interface,
                    "physicalType": physical_type,
                    "ioType": "Output",
                    "hardwarePortNumber": hardware_port,
                    "packetFormat": "188"
                }
            ]
        })
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': self.TOKEN
        }

        # Send request
        response = requests.put(url, headers=headers, data=payload, verify=False)
        print(f"Response: {response.status_code}, {response.text}")

        # Check if the status is not 202
        response.raise_for_status()  # Raises an error for HTTP status codes 4xx/5xx


    # TODO
    def post_descramble_service(self):
        print(f"Posting descramble service to {self.ip} with payload: {self.file_name}")
        url = f"https://{self.ip}:8443/api/v2/Descrambling?results=false"
        self.post(url=url)


    # TODO
    def post_transcode_service(self):
        print(f"Posting transcode service to {self.ip} with payload: {self.file_name}")
        url = f"https://{self.ip}:8443/api/v2/LinearTranscodeServices?results=false"
        self.post(url)


    # TODO
    def post_service_route(self):
        print(f"Posting service route of service to {self.ip} with payload: {self.file_name}")
        url = f"https://{self.ip}:8443/api/v2/OutputServiceRoutings?results=false"
        self.post(url)

    
    def post_ts_route(self):
        print(f"Posting ts route to {self.ip} with payload: {self.file_name}")
        url = f"https://{self.ip}:8443/api/v2/OutputTSRoutings?results=false"
        self.post(url)


    def factory_reset(self):
        print(f"[INFO] Factory resetting {self.ip}")
        url = f"https://{self.ip}:8443/api/v2/Restart?results=false"
        body = {
            "restartAction": "ClearSettings"
        }
        
        self.put(url, body)

        try:
            self.cleanup()
        except Exception as e:
            print("[ERROR] Failed to clean password... credentials may be wrong")


    def force_arp_update(self):
        print("Forcing arp update on switch")
        device = {
            "device_type": "cisco_ios",  # Change based on switch vendor (e.g., "hp_procurve", "juniper", etc.)
            "host": switch_ip,
            "username": switch_username,
            "password": switch_password,
            "fast_cli": False,
        }

        print("Connect to the switch")
        net_connect = ConnectHandler(**device)
        
        print("Run ping command")
        output = net_connect.send_command(f"ping {self.ip}")
        
        print(output)  # Print the result

        print("Close connection")
        net_connect.disconnect()

        print("Arp update complete")


    def is_ip_reachable(self, duration=60):
        """
        Check if an IP is reachable for a specified duration.

        :param ip: IP address to check
        :param duration: Total time (in seconds) to keep checking
        :return: True if the device becomes reachable, False otherwise
        """
        param = "-n" if platform.system().lower() == "windows" else "-c"
        start_time = time.time()

        while time.time() - start_time < duration:
            command = ["ping", param, "1", str(self.ip)]
            try:
                clear_arp_cache(switch_ip, switch_username, switch_password, switch_enable_password)
                self.force_arp_update()
                subprocess.check_call(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                print("Meg is reachable. Continuing with payload")
                return True  # Device is reachable
            except subprocess.CalledProcessError:
                time.sleep(1)  # Wait before retrying
            except Exception as e:
                print(f"Error checking IP reachability: {e}")
                print("TRYING AGAIN")   
                time.sleep(1)  # Wait before retrying
        
        # If it reaches here, the MEG is not reachable
        raise Exception(f"MEG at {self.ip} is not reachable after {duration} seconds.")
    

    def get_license_status(self):
        url = f"https://{self.ip}:8443/api/v1/license/status"
        return self.get(url)


    def get_host_id(self):
        response = self.get_license_status()
        return response["hostData"]["hostId"]


    def find_license_file(license_dir, host_id):
        """
        Searches for a license file that corresponds to the given host_id.

        :param license_dir: Directory containing license files
        :param host_id: The host ID to match with a file
        :return: Full path of the matching license file or None if not found
        """

        for filename in os.listdir(license_dir):
            if host_id in filename:  # Assuming filenames contain the host ID
                return os.path.join(license_dir, filename)
        raise Exception("No License File Found")  # No matching file found


    def scp_file_netmiko(self, local_path, remote_path):
        with ConnectHandler(**self.device) as ssh_conn:
            transfer_result = file_transfer(
                ssh_conn,
                source_file=local_path,
                dest_file=remote_path,
                file_system="/root/",  # Adjust if needed
                direction="put",
            )

        return transfer_result


    def confirm_license(self, license_file, timeout=30, retry_interval=1):
        """Keeps retrying the validation of the JSON data until success or timeout."""
        required_functions = self.extract_required_functions(license_file)  # Only get this once
        start_time = time.time()

        while time.time() - start_time < timeout:
            json_data = self.get_license_status()  # Assuming this method is defined elsewhere
            
            if self.validate_functions(json_data=json_data, required_functions=required_functions):
                return True

            time.sleep(retry_interval)  # Wait before retrying

        raise Exception(f"License did not update in alloted time: {timeout}")  # Timeout reached, license check failed


    def extract_required_functions(license_file):
        """Extracts function names from the license file."""
        required_functions = []
        with open(license_file, 'r') as file:
            for line in file:
                match = re.search(r'FEATURE\s+(\S+)', line)
                if match:
                    required_functions.append(match.group(1))
        return required_functions


    def validate_functions(json_data, required_functions):
        """Validates that required functions exist in the JSON response with a count of at least 1."""
        if "functions" not in json_data:
            return False

        function_dict = {func["entitlementTag"]: func["functionCount"] for func in json_data["functions"]}

        for func_name in required_functions:
            if function_dict.get(func_name, 0) < 1:
                return False

        return True


    def upload_license(self, pwExpire, license_dir):
        if pwExpire:
            self.change_expired_password()
        self.reset_password_ssh()
        self.post_auth()
        host_id = self.get_host_id()
        license_file = self.find_license_file(host_id=host_id, license_dir=license_dir)
        self.scp_file_netmiko(local_path=license_file, remote_path="/var/meg/synalic")
        self.confirm_license(license_file=license_file)
        self.cleanup()


    
# meg = MegManager("/Users/ajones/Documents/Synamedia/git/MAGGIE/Templates/Decode_DEMO.json", None, None)
# meg.prechecks()
# # meg.confirm_rest_service()
# meg.post_auth()
# meg.post_decode_service()