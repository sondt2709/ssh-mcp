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
async def execute_ssh_command(
    hostname: str, 
    command: str, 
    timeout: int = 30, 
    max_length: int = 1000
) -> str:
    """Execute a command on a remote host via SSH.

    Args:
        hostname: The hostname/alias of the target server as configured in SSH config
        command: The shell command to execute on the remote host
        timeout: SSH connection and command timeout in seconds (default: 30, max: 300)
        max_length: Maximum length of stdout/stderr output in characters (default: 1000, max: 10,000,000)

    Returns:
        Formatted string containing command output or error information
    """
    try:
        client = get_ssh_client()
        result = client.execute_command(hostname, command, timeout, max_length)

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
async def test_ssh_connection(hostname: str, timeout: int = 30) -> str:
    """Test SSH connection to a remote host without executing any commands.

    Args:
        hostname: The hostname/alias of the target server to test
        timeout: SSH connection timeout in seconds (default: 30, max: 300)

    Returns:
        String indicating whether the connection was successful or failed
    """
    try:
        client = get_ssh_client()
        host_config = client.config.get_host_config(hostname)

        if not host_config:
            return f"ERROR: Host '{hostname}' not found in configuration."

        # Validate timeout parameter
        command_timeout = min(max(timeout, 1), 300)  # 1s to 5 minutes

        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        sock = None
        # Check if proxy config exists for this host
        proxy = client.proxy_config.get(hostname) if client.proxy_config else None
        if proxy:
            try:
                import socks

                sock = socks.socksocket()
                sock.set_proxy(
                    proxy_type=socks.SOCKS5,
                    addr=proxy.host,
                    port=proxy.port,
                    username=proxy.username,
                    password=proxy.password,
                )
                sock.connect(
                    (
                        host_config.get("hostname", hostname),
                        int(host_config.get("port", 22)),
                    )
                )
            except Exception:
                return f"ERROR: Failed to connect via SOCKS5 proxy for {hostname}"

        try:
            ssh_client.connect(
                hostname=host_config.get("hostname", hostname),
                port=host_config.get("port", 22),
                username=host_config.get("user", os.getenv("USER")),
                key_filename=host_config.get("identityfile"),
                timeout=command_timeout,
                sock=sock,
            )

            return f"SUCCESS: Connection to {hostname} successful"

        except Exception as e:
            return f"ERROR: Connection to {hostname} failed: {str(e)}"
        finally:
            ssh_client.close()
            if sock:
                try:
                    sock.close()
                except Exception:
                    pass

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
