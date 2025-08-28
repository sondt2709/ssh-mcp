"""SSH client module for managing SSH connections and command execution."""

import os
import traceback
from typing import Any, Dict, List, Optional

import paramiko


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
    """SSH client for executing commands on remote hosts."""

    def __init__(self, config: SSHConfig):
        """Initialize SSH client with configuration."""
        self.config = config

    def execute_command(self, hostname: str, command: str) -> Dict[str, Any]:
        """Execute a command on a remote host via SSH.

        Args:
            hostname: The hostname of the target server
            command: The command to execute

        Returns:
            Dictionary containing execution results with keys:
            - success: Boolean indicating if command executed successfully
            - stdout: Command output (if successful)
            - stderr: Error output (if any)
            - exit_code: Command exit code (if successful)
            - error: Error message (if failed)
        """
        host_config = self.config.get_host_config(hostname)

        if not host_config:
            return {
                "success": False,
                "error": f"Host configuration not found for hostname: {hostname}",
            }

        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            ssh_client.connect(
                hostname=host_config.get("hostname", hostname),
                port=host_config.get("port", 22),
                username=host_config.get("user", os.getenv("USER")),
                key_filename=host_config.get("identityfile"),
                timeout=30,
            )

            stdin, stdout, stderr = ssh_client.exec_command(command)

            stdout_data = stdout.read().decode("utf-8")
            stderr_data = stderr.read().decode("utf-8")
            exit_code = stdout.channel.recv_exit_status()

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

    def list_hosts(self) -> List[str]:
        """List all configured hosts."""
        return self.config.list_hosts()
