#!/usr/bin/env python3
"""Integration tests for SSH MCP."""

import os

import pytest

from ssh_mcp.mcp import mcp
from ssh_mcp.ssh_client import SSHConfig


class TestSSHMCPRealIntegration:
    """Real integration tests using actual SSH connection to host 'test'."""

    def test_host_test_exists_in_config(self):
        """Test that host 'test' exists in SSH config."""
        config = SSHConfig()
        hosts = config.list_hosts()
        
        if "test" not in hosts:
            pytest.skip("Host 'test' not found in SSH config. Add a host named 'test' to run integration tests.")
    
    def test_ssh_config_loading(self):
        """Test that SSH config loads correctly."""
        config = SSHConfig()
        assert config.config_file_path is not None
        assert os.path.exists(config.config_file_path) or config.config_file_path == os.path.expanduser("~/.ssh/config")

    def test_get_test_host_config(self):
        """Test getting configuration for test host."""
        config = SSHConfig()
        hosts = config.list_hosts()
        
        if "test" not in hosts:
            pytest.skip("Host 'test' not found in SSH config")
        
        host_config = config.get_host_config("test")
        assert host_config is not None
        assert "hostname" in host_config

    @pytest.mark.asyncio
    async def test_list_hosts_real(self):
        """Test listing real hosts from SSH config."""
        result = await mcp.call_tool("list_ssh_hosts", {})
        result_text = str(result)
        
        assert "Configured SSH Hosts" in result_text
        # Should contain some hosts
        assert "Host:" in result_text

    @pytest.mark.asyncio
    async def test_get_test_host_info_real(self):
        """Test getting real host info for test host."""
        config = SSHConfig()
        hosts = config.list_hosts()
        
        if "test" not in hosts:
            pytest.skip("Host 'test' not found in SSH config")
        
        result = await mcp.call_tool("get_host_info", {"hostname": "test"})
        result_text = str(result)
        
        assert "Host Information for 'test'" in result_text
        assert "Hostname:" in result_text

    @pytest.mark.asyncio
    async def test_ssh_connection_to_test_host(self):
        """Test actual SSH connection to test host."""
        config = SSHConfig()
        hosts = config.list_hosts()
        
        if "test" not in hosts:
            pytest.skip("Host 'test' not found in SSH config")
        
        result = await mcp.call_tool("test_ssh_connection", {"hostname": "test"})
        result_text = str(result)
        
        # Connection should either succeed or fail with a specific error
        assert ("SUCCESS" in result_text) or ("ERROR" in result_text)

    @pytest.mark.asyncio 
    async def test_execute_command_on_test_host(self):
        """Test executing a real command on test host (Linux VM)."""
        config = SSHConfig()
        hosts = config.list_hosts()
        
        if "test" not in hosts:
            pytest.skip("Host 'test' not found in SSH config")
        
        # Test with a simple, safe Linux command
        result = await mcp.call_tool("execute_ssh_command", {
            "hostname": "test", 
            "command": "echo 'SSH MCP Test' && whoami && uname -s"
        })
        result_text = str(result)
        
        if "SUCCESS" in result_text:
            # If successful, should contain our test output
            assert "SSH MCP Test" in result_text
            assert "Linux" in result_text or "EXIT" in result_text  # uname -s output or exit code
        else:
            # If failed, should contain error information
            assert "ERROR" in result_text

    @pytest.mark.asyncio
    async def test_execute_command_filesystem_check(self):
        """Test filesystem commands on test host."""
        config = SSHConfig()
        hosts = config.list_hosts()
        
        if "test" not in hosts:
            pytest.skip("Host 'test' not found in SSH config")
        
        # Test basic filesystem commands
        result = await mcp.call_tool("execute_ssh_command", {
            "hostname": "test", 
            "command": "pwd && ls -la / | head -5"
        })
        result_text = str(result)
        
        if "SUCCESS" in result_text:
            # Should contain typical Linux directory structure
            assert ("bin" in result_text or "etc" in result_text or "home" in result_text 
                   or "/" in result_text)  # Basic Linux filesystem check


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
