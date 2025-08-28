from dotenv import load_dotenv

load_dotenv()


def main():
    from ssh_mcp import mcp

    mcp.run()
