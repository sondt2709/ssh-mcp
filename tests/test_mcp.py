from unittest.mock import Mock, patch

import pytest

from ssh_mcp.mcp import mcp


class TestSSHMCPTools:
    """Test SSH MCP tools with minimal mocking."""

    @pytest.mark.asyncio
    async def test_execute_ssh_command_success(self):
        """Test successful SSH command execution via MCP tool."""
        mock_client = Mock()
        mock_client.execute_command.return_value = {
            "success": True,
            "stdout": "test output",
            "stderr": "",
            "exit_code": 0,
        }

        with patch("ssh_mcp.mcp.get_ssh_client", return_value=mock_client):
            result = await mcp.call_tool(
                "execute_ssh_command", {"hostname": "test-host", "command": "echo test"}
            )

        assert "SUCCESS" in str(result)
        assert "test output" in str(result)

    @pytest.mark.asyncio
    async def test_execute_ssh_command_failure(self):
        """Test SSH command execution failure via MCP tool."""
        mock_client = Mock()
        mock_client.execute_command.return_value = {
            "success": False,
            "error": "Connection failed",
        }

        with patch("ssh_mcp.mcp.get_ssh_client", return_value=mock_client):
            result = await mcp.call_tool(
                "execute_ssh_command", {"hostname": "nonexistent", "command": "echo test"}
            )

        assert "ERROR" in str(result)
        assert "Connection failed" in str(result)

    @pytest.mark.asyncio
    async def test_list_ssh_hosts(self):
        """Test listing SSH hosts via MCP tool."""
        mock_client = Mock()
        mock_client.list_hosts.return_value = ["host1", "host2"]

        with patch("ssh_mcp.mcp.get_ssh_client", return_value=mock_client):
            result = await mcp.call_tool("list_ssh_hosts", {})

        assert "host1" in str(result)
        assert "host2" in str(result)

    @pytest.mark.asyncio
    async def test_get_host_info(self):
        """Test getting host information via MCP tool."""
        mock_client = Mock()
        mock_client.config.get_host_config.return_value = {
            "hostname": "192.168.1.100",
            "port": 22,
            "user": "testuser",
        }

        with patch("ssh_mcp.mcp.get_ssh_client", return_value=mock_client):
            result = await mcp.call_tool("get_host_info", {"hostname": "test-host"})

        assert "test-host" in str(result)
        assert "192.168.1.100" in str(result)
