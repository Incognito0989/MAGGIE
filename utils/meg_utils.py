from netmiko import ConnectHandler
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
    def __init__(self, payload, processing_type, service_dir):
        self.TOKEN = None
        self.ip = meg_ip
        self.processing_type = processing_type
        self.rest_username = meg_rest_username
        self.rest_password = meg_rest_password
        self.username = meg_username
        self.password = meg_password
        self.service_dir = service_dir
        self.payload = payload
        self.file_name = os.path.basename(self.payload)
        self.device = {
            "device_type": "linux",
            "host": self.ip,
            "username": "root",
            "password": "password",
            "session_log": "netmiko_debug.log",  # Logs session for debugging
        }

    def prechecks(self):
        self.change_expired_password()
        self.confirm_rest_service()
        self.make_rest_user()

    def change_expired_password(self):
        """Handle forced password change over SSH using pexpect and show terminal output."""

        ssh_command = f"ssh {self.device["username"]}@{self.device["host"]}"

        # Start the SSH session
        child = pexpect.spawn(ssh_command, encoding='utf-8')

        # Enable logging to stdout (prints all interactions)
        # child.logfile = sys.stdout  # Show output in the terminal
        print("Starting SSH session...")

        try:
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

            # Send pub id to authkeys
            print("Adding Maggie's public key")
            child.expect(']#')
            child.sendline(f'echo "{pub_key}" >> ~/.ssh/authorized_keys')

            child.expect(']#')
            child.sendline('passwd')

            # Expect password prompts
            child.expect('New password: ', timeout=15)
            child.sendline(self.device["password"])
            child.expect('Retype new password: ', timeout=15)
            child.sendline(self.device["password"])

            # Confirm success
            child.expect(['password updated successfully', pexpect.TIMEOUT], timeout=15)

        except pexpect.exceptions.TIMEOUT:
            print(f"Timeout occurred. Last received output: {child.before}")  # Show last received text before timeout
            child.close()
            return

        # Wait for success message
        child.expect(['successfully', pexpect.TIMEOUT], timeout=30)
        print(f"Final response: {child.after}")  # Print final confirmation or timeout

        child.close()


    def reset_password_ssh(self):
        """Log in again with temp password and reset to original password."""
        ssh_command = f"ssh {self.device["username"]}@{self.device["host"]}"

        child = pexpect.spawn(ssh_command, encoding='utf-8')
        # child.logfile = sys.stdout  # Print interactions

        try:
            child.expect('password: ', timeout=15)
            print("Logging in again to reset password.")
            child.sendline(self.password)

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

        except pexpect.exceptions.TIMEOUT:
            print(f"Timeout occurred while resetting password. Last output: {child.before}")

        child.close()
        print("Password reset completed.")


    def confirm_rest_service(self):
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

    def make_rest_user(self):
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

    def post(self, url):
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': self.TOKEN
        }

        with open(self.payload, "r") as file:
            self.payload = json.load(file)

        response = requests.request("POST", url, headers=headers, json=self.payload, verify=False)
        print(response.text)

        if 'errors' in response.text:
            return 'error'

    def process_service_for_ip(self):
        service_functions = {
            "Decode": self.post_decode_service,
            "Transcode": self.post_transcode_service,
            "Descramble": self.post_descramble_service
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

        try:
            response = requests.request("POST", url, headers=headers, json=cred, verify=False)
            self.TOKEN = response.json()['token']
            if self.TOKEN:
                print(f"SUCCESS, got token: {self.TOKEN}")
        except:
            print(f"Failed to get token for {self.ip}")

        if '"code": 401' in response.text:
            return 'error'
        return 'success'


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

        with open(self.payload, "r") as file:
            self.payload = json.load(file)

        print(self.payload)
        response = requests.request("POST", url, headers=headers, json=self.payload, verify=False)
        print(response.text)

        if 'errors' in response.text:
            return 'error'
        return 'success'

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

    def force_arp_update(self):
        print("Forcing arp update on switch")
        device = {
            "device_type": "cisco_ios",  # Change based on switch vendor (e.g., "hp_procurve", "juniper", etc.)
            "host": switch_ip,
            "username": switch_username,
            "password": switch_password,
            "fast_cli": False,
        }

        try:
            # Connect to the switch
            net_connect = ConnectHandler(**device)
            
            # Run ping command
            output = net_connect.send_command(f"ping {self.ip}")
            
            print(output)  # Print the result

            # Close connection
            net_connect.disconnect()

            print("Arp update complete")
        except Exception as e:
            print(f"SSH Error: {e}")

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
                return True  # Device is reachable
            except subprocess.CalledProcessError:
                time.sleep(1)  # Wait before retrying
        
        return False  # Timeout reached without success
    
# meg = MegManager("/Users/ajones/Documents/Synamedia/git/MAGGIE/Templates/Decode_DEMO.json", None, None)
# meg.prechecks()
# # meg.confirm_rest_service()
# meg.post_auth()
# meg.post_decode_service()