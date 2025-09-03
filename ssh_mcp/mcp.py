"""SSH MCP server for managing SSH connections and executing commands on remote hosts."""

import os
import traceback

import paramiko
from mcp.server.fastmcp import FastMCP

from ssh_mcp.ssh_client import SSHClient, SSHConfig

mcp = FastMCP(
    name="ssh-mcp",
    instructions="A Model Context Protocol for managing and interacting with multiple virtual machines over SSH",
)

_ssh_client = None


def get_ssh_client() -> SSHClient:
    """Get or create SSH client instance."""
    global _ssh_client
    if _ssh_client is None:
        try:
            config = SSHConfig()
            _ssh_client = SSHClient(config)
        except Exception:
            traceback.print_exc()
            raise
    return _ssh_client


@mcp.tool()
async def execute_ssh_command(hostname: str, command: str) -> str:
    """Execute a command on a remote host via SSH.

    Args:
        hostname: The hostname/alias of the target server as configured in SSH config
        command: The shell command to execute on the remote host

    Returns:
        Formatted string containing command output or error information
    """
    try:
        client = get_ssh_client()
        result = client.execute_command(hostname, command)

        if result["success"]:
            output = f"""SUCCESS: Command executed on {hostname}
Command: {command}
Exit Code: {result["exit_code"]}

STDOUT:
{result["stdout"]}"""

            if result["stderr"]:
                output += f"\n\nSTDERR:\n{result['stderr']}"

            return output
        else:
            return f"ERROR: Failed to execute command on {hostname}\nError: {result['error']}"

    except Exception as e:
        traceback.print_exc()
        return f"ERROR: Failed to execute command: {str(e)}"


@mcp.tool()
async def list_ssh_hosts() -> str:
    """List all configured SSH hosts.

    Returns:
        Formatted string containing all configured hosts
    """
    try:
        client = get_ssh_client()
        hosts = client.list_hosts()

        if not hosts:
            return "No SSH hosts configured."

        output = "Configured SSH Hosts:\n" + "=" * 25 + "\n\n"
        for host in hosts:
            output += f"Host: {host}\n"

        return output

    except Exception as e:
        traceback.print_exc()
        return f"ERROR: Failed to list hosts: {str(e)}"


@mcp.tool()
async def get_host_info(hostname: str) -> str:
    """Get detailed information about a specific SSH host.

    Args:
        hostname: The hostname/alias of the target server

    Returns:
        Formatted string containing host configuration details
    """
    try:
        client = get_ssh_client()
        host_config = client.config.get_host_config(hostname)

        if not host_config:
            return f"ERROR: Host '{hostname}' not found in configuration."

        output = f"Host Information for '{hostname}':\n" + "=" * 35 + "\n\n"
        output += f"Hostname: {host_config.get('hostname', hostname)}\n"
        output += f"Port: {host_config.get('port', 22)}\n"
        output += f"User: {host_config.get('user', 'N/A')}\n"
        output += f"IdentityFile: {host_config.get('identityfile', 'N/A')}\n"

        return output

    except Exception as e:
        traceback.print_exc()
        return f"ERROR: Failed to get host information: {str(e)}"


@mcp.tool()
async def test_ssh_connection(hostname: str) -> str:
    """Test SSH connection to a remote host without executing any commands.

    Args:
        hostname: The hostname/alias of the target server to test

    Returns:
        String indicating whether the connection was successful or failed
    """
    try:
        client = get_ssh_client()
        host_config = client.config.get_host_config(hostname)

        if not host_config:
            return f"ERROR: Host '{hostname}' not found in configuration."

        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            ssh_client.connect(
                hostname=host_config.get("hostname", hostname),
                port=host_config.get("port", 22),
                username=host_config.get("user", os.getenv("USER")),
                key_filename=host_config.get("identityfile"),
                timeout=10,
            )

            return f"SUCCESS: Connection to {hostname} successful"

        except Exception as e:
            return f"ERROR: Connection to {hostname} failed: {str(e)}"
        finally:
            ssh_client.close()

    except Exception as e:
        traceback.print_exc()
        return f"ERROR: Failed to test connection: {str(e)}"


def run():
    """Run the SSH MCP server."""
    transport = os.getenv("MCP_TRANSPORT", "stdio")
    if transport == "sse":
        mcp.run(transport="sse")
    elif transport == "streamable-http":
        mcp.run(transport="streamable-http")
    else:
        mcp.run(transport="stdio")
