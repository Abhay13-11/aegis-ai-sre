"""
AEGIS Fault Injection CLI Utility
Allows manual or automated fault injection into the microservices testbed.
"""

import sys
import os
import requests
import argparse

def main():
    parser = argparse.ArgumentParser(description="Inject chaos fault into AEGIS testbed")
    parser.add_argument("--type", type=str, default="DB_POOL_EXHAUSTION",
                        choices=["DB_POOL_EXHAUSTION", "DB_LATENCY", "REDIS_FAILURE", "CPU_SPIKE", "MEMORY_LEAK", "SERVICE_CRASH"],
                        help="Chaos fault type")
    parser.add_argument("--target", type=str, default="inventory_service", help="Target service")
    parser.add_argument("--url", type=str, default="http://localhost:8000", help="AEGIS Backend API URL")
    args = parser.parse_args()

    payload = {
        "fault_type": args.type,
        "target_service": args.target,
        "params": {},
        "description": f"CLI Injected Fault: {args.type} on {args.target}"
    }

    try:
        res = requests.post(f"{args.url}/api/chaos/inject", json=payload)
        res.raise_for_status()
        data = res.json()
        print(f"\n[+] Successfully injected {args.type} onto {args.target}!")
        print(f"    Fault ID: {data['fault']['fault_id']}")
        if data.get("incident"):
            print(f"    Linked Incident: {data['incident']['incident_id']} ({data['incident']['title']})")
        print()
    except requests.exceptions.ConnectionError:
        print(f"\n[-] Error: AEGIS platform is not running at {args.url}.")
        print("    Start the platform with: python scripts/run_platform.py\n")

if __name__ == '__main__':
    main()
