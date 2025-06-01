# scripts/config_backup.py
# incorporating Netmiko and error handling

import netmiko # type: ignore
import datetime
import os
import yaml # type: ignore
import logging
import argparse
import sys
# from netmiko import ConnectHandler # type: ignore - Not strictly needed if using netmiko.ConnectHandler
from netmiko.exceptions import NetmikoTimeoutException, NetmikoAuthenticationException, NetmikoBaseException # type: ignore # Added NetmikoBaseException

# GLOBAL SETTING FOR DEBUGGING - CORRECTED PLACEMENT
# Set this to True to enable Netmiko session logging (highly recommended for debugging)
# Set to False when you don't need detailed session logs anymore (e.g., in production)
ENABLE_SESSION_LOGGING = True

def loadDevices(devices_file="data/devices.yaml"):
    """Loads device information from a YAML file.
    Args:
        devices_file (str): Path to the YAML file containing device info.
    Returns:
        list: A list of device dict, or None on error.
    """

    try:
        with open(devices_file, "r") as f:
            devices_data = yaml.safe_load(f)    #use safe_load
            # This line already correctly extracts from the 'devices' key
            return devices_data.get("devices", [])  #handles if "devices" key doesn't exist
    except FileNotFoundError:
        logging.error(f"Error: {devices_file} not found.")
        return None
    except yaml.YAMLError as e:
        logging.error(f"Error parsing YAML file: {e}")
        return None
    except Exception as e:
        logging.error(f"An unexpected error occurred while loading devices: {e}")
        return None

def backup_config(device, backup_dir):
    """Backs up the configuration of a single network device using Netmiko.

    Args:
        device (dict): A dictionary containing device information (name, host, username, password, device_type).
        backup_dir (str): The directory to save the backup to.
    """
    session_log_path = None
    if ENABLE_SESSION_LOGGING:
        # Create a specific directory for session logs if it doesn't exist
        session_log_dir = "debug_logs/sessions"
        os.makedirs(session_log_dir, exist_ok=True)
        timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        # Create a unique filename for the session log for this device
        session_log_path = os.path.join(session_log_dir, f"{device['name']}-{timestamp}_session.log")
        logging.debug(f"Session log for {device['name']} will be saved to {session_log_path}")

    # --- START OF CRUCIAL FIX & SESSION LOG INTEGRATION ---
    # Netmiko's ConnectHandler expects specific parameters.
    # We need to create a dictionary that only contains those parameters,
    # as the 'name' key from devices.yaml is not a valid Netmiko parameter.
    netmiko_device_params = {
        'host': device['host'],
        'username': device['username'],
        'password': device['password'],
        'device_type': device['device_type'],
        # You can add other Netmiko parameters here if needed, e.g.:
        # 'port': 22, # Default SSH port, good to be explicit if not 22
        # 'secret': device.get('secret'), # Use .get() to safely retrieve enable password if it might not exist
        # 'global_delay_factor': 2, # Can help with slow connections or large outputs
        # 'timeout': 10, # Connection timeout in seconds
    }

    # Add the session_log parameter only if ENABLE_SESSION_LOGGING is True
    if session_log_path:
        netmiko_device_params['session_log'] = session_log_path
    # --- END OF CRUCIAL FIX & SESSION LOG INTEGRATION ---

    try:
        logging.info(f"Connecting to {device['name']} ({device['host']})")
        # Now, Netmiko will receive only the parameters it expects
        with netmiko.ConnectHandler(**netmiko_device_params) as net_connect:
            net_connect.enable() # Attempt to enter enable mode
            config = net_connect.send_command("show running-config")
            timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
            backup_file = os.path.join(
                backup_dir, f"{device['name']}-{timestamp}.config"
            )
            with open(backup_file, "w") as f:
                f.write(config)
            logging.info(f"Configuration backed up for {device['name']} to {backup_file}")
        return True # Indicate success
    except NetmikoTimeoutException:
        logging.error(f"Timeout connecting to {device['name']} ({device['host']}). Possible issues: device off, network path blocked by firewall, incorrect IP, or high latency.")
        if session_log_path:
            logging.debug(f"Review session log at {session_log_path} for more details (it may be empty if connection failed early).")
        return False
    except NetmikoAuthenticationException:
        logging.error(f"Authentication failed for {device['name']} ({device['host']}). Check username, password, or enable password in devices.yaml. Device is reachable.")
        if session_log_path:
            logging.debug(f"Review session log at {session_log_path} for authentication handshake details.")
        return False
    except NetmikoBaseException as e: # Catches other Netmiko-specific errors (e.g., SSH, Read, EOF)
        logging.error(f"Netmiko specific error with {device['name']} ({device['host']}): {e}. This indicates a problem during the SSH/Telnet session setup or command execution.")
        if session_log_path:
            logging.debug(f"Review session log at {session_log_path} for Netmiko's interaction with the device.")
        return False
    except Exception as e: # Catches any other unexpected Python errors
        logging.error(f"An unexpected Python error occurred while backing up {device['name']} ({device['host']}): {e}. This might be a bug in the script itself.")
        if session_log_path:
            logging.debug(f"Review session log at {session_log_path} as well for clues.")
        return False


def main():
    """
    Main function to parse arguments, load devices, and backup configurations.
    """
    parser = argparse.ArgumentParser(
        description="Backup network device configurations using Netmiko."
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose output (debug logging).",
    )
    parser.add_argument(
        "-d",
        "--devices",
        default="data/devices.yaml", #set default
        help="Path to the devices.yaml file"
    )
    parser.add_argument(
        "-b",
        "--backup_dir",
        default="backups",
        help="Path to the backup directory"
    )
    args = parser.parse_args()

    # Configure logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),  # Output to console
        ],
    )
    devices_file = args.devices
    backup_dir = args.backup_dir

    # Create necessary directories
    os.makedirs(backup_dir, exist_ok=True)
    # This check now works because ENABLE_SESSION_LOGGING is defined globally at the top
    if ENABLE_SESSION_LOGGING:
        os.makedirs("debug_logs/sessions", exist_ok=True)

    devices = loadDevices(devices_file)
    if devices is None:
        logging.error("Failed to load devices. Exiting.")
        sys.exit(1)

    for device in devices:
        backup_successful = backup_config(device, backup_dir)
        if not backup_successful:
            logging.warning(f"Backup failed for {device['name']}. Continuing with next device...")
    logging.info("Backup process completed.")


if __name__ == "__main__":
    main() 
