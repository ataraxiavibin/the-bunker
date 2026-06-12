# parser.py

import argparse

def get_args(service_name: str, description: str, choices: list[str] = None):
    parser = argparse.ArgumentParser(description=f"{service_name} is a {description}. this is generated within shared/parser")
    parser.add_argument("action", nargs="?", choices=choices, help="action to perform")
    parser.add_argument("--json", action="store_true", help="print for bunker")

    return parser.parse_args()

