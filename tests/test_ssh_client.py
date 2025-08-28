import os

from ssh_mcp.ssh_client import SSHClient, SSHConfig


class TestSSHConfigBasic:
    """Basic tests for SSH configuration management."""

    def test_default_config_path(self):
        """Test using default SSH config path."""
        config = SSHConfig()
        assert config.config_file_path == os.path.expanduser("~/.ssh/config")

    def test_custom_config_path(self, monkeypatch):
        """Test using custom SSH config path."""
        custom_path = "/custom/ssh/config"
        monkeypatch.setenv("SSH_CONFIG_PATH", custom_path)
        config = SSHConfig()
        assert config.config_file_path == custom_path

    def test_ssh_client_initialization(self):
        """Test SSH client initialization with config."""
        config = SSHConfig()
        client = SSHClient(config)
        assert client.config == config
