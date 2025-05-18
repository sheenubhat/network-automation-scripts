# incorporating Netmiko and error handling

import netmiko
import datetime
import os
import yaml
import logging
import argparse
import sys
from netmiko import ConnectHandler
from netmiko.exceptions import NetmikoTimeoutException, NetmikoAuthenticationException

def loadDevices(devices_file="data/devices.yaml"):
    """Loads device information from a YAML file.
    Args:
        devices_file (str): Path to the YAML file containing device info.
    Returns:
        list: A list of device dict, or None on error.
    """

    try:
        with open(devices_file, "r") as f:
            devices_data=yaml.safe_load(f)     #use safe_load
            return devices_data.get("devices", [])   #handles if "devices" key doesn't exist
    except FileNotFoundError:
        logging.error(f"Error: {devices_file} not found.")
        return None
    except yaml.YAMLError as e:
        logging.error(f"Error parsing YAML file: {e}")
        return None
    except Exception as e:
        logging.error(f"An expected error occurred: {e}")
        return None
    
def backup_config(device, backup_dir):
    """Backs up the configuration of a single network device using Netmiko.

    Args:
        device (dict): A dictionary containing device information (host, username, password, type).
        backup_dir (str): The directory to save the backup to.
    """
    try:
        logging.info(f"Connecting to {device['name']} ({device['host']})")
        with netmiko.ConnectHandler(**device) as net_connect:
            net_connect.enable()
            config = net_connect.send_command("show running-config")
            timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
            backup_file = os.path.join(
                backup_dir, f"{device['name']}-{timestamp}.config"
            )
            with open(backup_file, "w") as f:
                f.write(config)
            logging.info(f"Configuration backed up for {device['name']} to {backup_file}")
        return True # Indicate success
    except netmiko.NetmikoTimeoutException:
        logging.error(f"Timeout connecting to {device['name']} ({device['host']})")
        return False
    except netmiko.NetmikoAuthenticationException:
        logging.error(
            f"Authentication failed for {device['name']} ({device['host']})"
        )
        return False
    # except netmiko.NetmikoSSHException as e:
    #     logging.error(f"SSH error with {device['name']} ({device['host']}): {e}")
    #     return False
    # except Exception as e:
    #     logging.error(
    #         f"An error occurred while backing up {device['name']} ({device['host']}): {e}"
    #     )
    #     return False  # Ensure a return value in all error cases



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

    devices = loadDevices(devices_file)
    if devices is None:
        logging.error("Failed to load devices. Exiting.")
        sys.exit(1)

    os.makedirs(backup_dir, exist_ok=True)

    for device in devices:
        backup_successful = backup_config(device, backup_dir)
        if not backup_successful:
            logging.warning(f"Backup failed for {device['name']}.  Continuing...")
    logging.info("Backup process completed.")


if __name__ == "__main__":
    main()
    
