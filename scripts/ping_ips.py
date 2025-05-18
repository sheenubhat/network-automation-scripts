


import subprocess
import argparse
import logging
import sys

def ping_host(host):

    """"
    Pings a single host.
    Args: 
        host (str): The hostname or IP address to ping.
    Returns:
        bool: True if the host is reachable, False otherwise.
    """



#Use subprocess.run for better contro; and error handling
    try:
        result = subprocess.run(
            ["ping" , "-c" , "1" , host],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,       #raise an exception for non-zero exit code
        )
        logging.info(f"Successfully pinged {host}")
        return True
    except subprocess.CalledProcessError:
        logging.warning(f"Failed to ping {host}")
        return False                                   # Ensure a return value in all error cases
    
def main():
    """"
    Main function to parse arguments and ping hosts.
    """
    parser = argparse.ArgumentParser(
        description="Ping multiple hosts from a file or a single host."

    )
    parser.add_argument(
        "hosts",
        nargs="*",
        help="List of hosts to ping, or a single host. If no hosts are provided and -f is not used, defaults to 127.0.0.1",
    )
    parser.add_argument(
        "-f",
        "--file",
        help="Path to file containing a list of hosts to ping(one per line).",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose output (debug logging).",
    )

    args = parser.parse_args()

    #Configure logging
    if args.file:
        try:
            with open(args.file, "r") as f:
                hosts_to_ping = [line.strip() for line in f]
        except FileNotFoundError:
            logging.error(f"Error reading file: {e}")
            sys.exit(1)
    elif args.hosts:
        hosts_to_ping = args.hosts
    else:
        hosts_to_ping = ["127.0.0.1"]     #default

    if not hosts_to_ping:
        logging.warning("No hosts to ping.")
        sys.exit(0)

    for host in hosts_to_ping:
        ping_host(host)

if __name__== "__main__":
    main()

