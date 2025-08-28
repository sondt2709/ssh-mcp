#!/usr/bin/env python3
"""Command line interface for SSH MCP direct usage."""

import asyncio
import sys
import traceback

from ssh_mcp.ssh_client import SSHClient, SSHConfig


def print_usage():
    """Print usage information."""
    print('Usage: uv run cli.py <host> "<command_to_execute>"')
    print("\nExamples:")
    print('  uv run cli.py web-server-01 "ls -l /home/admin"')
    print('  uv run cli.py db-server-01 "df -h"')
    print("\nMake sure SSH config is set up in ~/.ssh/config")


async def main():
    """Main entry point for direct CLI usage."""
    if len(sys.argv) != 3:
        print_usage()
        sys.exit(1)

    hostname = sys.argv[1]
    command = sys.argv[2]

    try:
        config = SSHConfig()
        client = SSHClient(config)

        result = client.execute_command(hostname, command)

        if result["success"]:
            print(f"SUCCESS: Command executed on {hostname}")
            print(f"Exit Code: {result['exit_code']}")
            print("\nOutput:")
            print(result["stdout"])

            if result["stderr"]:
                print("\nErrors:")
                print(result["stderr"])
        else:
            print(f"ERROR: Failed to execute command on {hostname}")
            print(f"Error: {result['error']}")
            sys.exit(1)

    except Exception:
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
