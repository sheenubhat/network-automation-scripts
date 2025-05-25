


from cmath import e
import subprocess
import argparse
import logging
import sys
import yaml  # Import the PyYAML library

def ping_host(host):
    """
    Pings a single host.

    Args:
        host (str): The hostname or IP address to ping.

    Returns:
        bool: True if the host is reachable, False otherwise.
    """
    try:
        # Use subprocess.run for better control and error handling
        result = subprocess.run(
            ["ping", "-c", "1", host],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
        )
        logging.info(f"Successfully pinged {host}")
        return True
    except subprocess.CalledProcessError:
        logging.warning(f"Failed to ping {host}")
        return False
    except Exception as e:
        logging.error(f"An error occurred while pinging {host}: {e}")
        return False

def main():
    """
    Main function to parse arguments and ping hosts from a YAML file.
    """
    parser = argparse.ArgumentParser(
        description="Ping multiple hosts from a file."
    )
    parser.add_argument(
        "-f",
        "--file",
        required=True,  # Make the file argument required
        help="Path to a YAML file containing device information.",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose output (debug logging).",
    )
    args = parser.parse_args()

    # Configure logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
        ],
    )

    try:
        with open(args.file, "r") as f:
            devices_data = yaml.safe_load(f)  # Use yaml.safe_load()
            devices = devices_data.get("devices", [])  # Get the list of devices
            if not devices:
                logging.warning("No devices found in the YAML file.")
                sys.exit(0)
    except FileNotFoundError:
        logging.error(f"File not found: {args.file}")
        sys.exit(1)
    except yaml.YAMLError as e:
        logging.error(f"Error parsing YAML file: {e}")
        sys.exit(1)
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        sys.exit(1)

    for device in devices:
        if "host" in device:  # Check if 'host' key exists
            host = device["host"]
            ping_host(host)
        else:
            logging.warning(f"Device missing 'host' key: {device}")

if __name__ == "__main__":
    main()

