"""SSH client module for managing SSH connections and command execution, with optional SOCKS5 proxy support."""

import json
import os
import traceback
from typing import Any, Dict, List, Optional

import paramiko
import socks

from ssh_mcp.model.proxy import ProxyConfig


class SSHConfig:
    """Manages SSH configuration from SSH config file."""

    def __init__(self):
        """Initialize SSH configuration by loading from SSH config file."""
        self.config_file_path = os.getenv(
            "SSH_CONFIG_PATH", os.path.expanduser("~/.ssh/config")
        )
        self.ssh_config = self._load_ssh_config()

    def _load_ssh_config(self) -> paramiko.SSHConfig:
        """Load SSH configuration from config file."""
        try:
            ssh_config = paramiko.SSHConfig()
            if os.path.exists(self.config_file_path):
                with open(self.config_file_path, "r") as f:
                    ssh_config.parse(f)
            return ssh_config
        except Exception:
            traceback.print_exc()
            return paramiko.SSHConfig()

    def get_host_config(self, hostname: str) -> Optional[Dict[str, Any]]:
        """Get configuration for a specific host by hostname."""
        try:
            return self.ssh_config.lookup(hostname)
        except Exception:
            traceback.print_exc()
            return None

    def list_hosts(self) -> List[str]:
        """List all configured host names."""
        try:
            return list(self.ssh_config.get_hostnames())
        except Exception:
            traceback.print_exc()
            return []


class SSHClient:
    """SSH client for executing commands on remote hosts, with optional SOCKS5 proxy support."""

    def __init__(self, config: SSHConfig):
        """Initialize SSH client with configuration and optional proxy config."""
        self.config = config
        self.proxy_config = self._load_proxy_config()

    def _load_proxy_config(self) -> Optional[dict[str, ProxyConfig]]:
        """Load proxy config from PROXY_CONFIG_PATH env if set."""
        proxy_path = os.getenv("PROXY_CONFIG_PATH")
        if proxy_path and os.path.exists(proxy_path):
            try:
                with open(proxy_path, "r") as f:
                    config: dict[str, Any] = json.load(f)
                    return {k: ProxyConfig.model_validate(v) for k, v in config.items()}
            except Exception:
                traceback.print_exc()
        return None

    def execute_command(
        self, 
        hostname: str, 
        command: str, 
        timeout: int = 30, 
        max_length: int = 1000
    ) -> Dict[str, Any]:
        """Execute a command on a remote host via SSH, with optional SOCKS5 proxy support.
        
        Args:
            hostname: The hostname of the target server
            command: The command to execute
            timeout: SSH connection and command timeout in seconds (max 300)
            max_length: Maximum length of stdout/stderr output in characters (max 10,000,000)
        """
        # Validate parameters
        command_timeout = min(max(timeout, 1), 300)  # 1s to 5 minutes
        max_stdout_length = min(max(max_length, 1), 10_000_000)  # 1 to 10M chars

        host_config = self.config.get_host_config(hostname)

        if not host_config:
            return {
                "success": False,
                "error": f"Host configuration not found for hostname: {hostname}",
            }

        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        sock: socks.socksocket | None = None
        proxy = self.proxy_config.get(hostname) if self.proxy_config else None
        if proxy:
            try:
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
                traceback.print_exc()
                return {
                    "success": False,
                    "error": "Failed to connect via SOCKS5 proxy.",
                }

        try:
            ssh_client.connect(
                hostname=host_config.get("hostname", hostname),
                port=host_config.get("port", 22),
                username=host_config.get("user", os.getenv("USER")),
                key_filename=host_config.get("identityfile"),
                timeout=command_timeout,
                sock=sock,
            )

            stdin, stdout, stderr = ssh_client.exec_command(
                command, timeout=command_timeout
            )

            stdout_data = stdout.read().decode("utf-8")
            stderr_data = stderr.read().decode("utf-8")
            exit_code = stdout.channel.recv_exit_status()

            # Truncate output if it exceeds max length
            if len(stdout_data) > max_stdout_length:
                stdout_data = stdout_data[:max_stdout_length] + "... (truncated)"
            if len(stderr_data) > max_stdout_length:
                stderr_data = stderr_data[:max_stdout_length] + "... (truncated)"

            return {
                "success": True,
                "stdout": stdout_data,
                "stderr": stderr_data,
                "exit_code": exit_code,
            }

        except Exception as e:
            traceback.print_exc()
            return {"success": False, "error": str(e)}

        finally:
            ssh_client.close()
            if sock:
                try:
                    sock.close()
                except Exception:
                    pass

    def list_hosts(self) -> List[str]:
        """List all configured hosts."""
        return self.config.list_hosts()
