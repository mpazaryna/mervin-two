#!/usr/bin/env python3
"""
MCP Test Client

A Python client for testing the MCP Learning Server without Claude Desktop.
This client communicates directly with the MCP server using the stdio protocol.
"""

import json
import subprocess
import sys
import time
import threading
from typing import Dict, Any, Optional, List
from queue import Queue, Empty
import uuid


class MCPTestClient:
    """
    Test client for MCP Learning Server.
    
    Communicates with the server via subprocess and stdio protocol.
    """
    
    def __init__(self, server_command: List[str] = None):
        """
        Initialize the MCP test client.
        
        Args:
            server_command: Command to start the MCP server
        """
        self.server_command = server_command or ["python", "-m", "mcp_server", "--debug"]
        self.process = None
        self.response_queue = Queue()
        self.pending_requests = {}
        self.running = False
        self.reader_thread = None
        self.initialized = False
        
    def start_server(self) -> bool:
        """
        Start the MCP server process.
        
        Returns:
            True if server started successfully, False otherwise
        """
        try:
            print(f"Starting MCP server with command: {' '.join(self.server_command)}")
            self.process = subprocess.Popen(
                self.server_command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=0
            )
            
            # Start reader thread
            self.running = True
            self.reader_thread = threading.Thread(target=self._read_responses, daemon=True)
            self.reader_thread.start()
            
            # Wait a moment for server to start
            time.sleep(1)
            
            # Check if process is still running
            if self.process.poll() is not None:
                stderr_output = self.process.stderr.read()
                print(f"Server failed to start. Error: {stderr_output}")
                return False
                
            print("✅ MCP server started successfully")
            return True
            
        except Exception as e:
            print(f"❌ Failed to start server: {e}")
            return False
    
    def _read_responses(self):
        """Read responses from the server in a separate thread."""
        while self.running and self.process and self.process.poll() is None:
            try:
                line = self.process.stdout.readline()
                if not line:
                    break
                    
                line = line.strip()
                if not line:
                    continue
                    
                try:
                    response = json.loads(line)
                    self.response_queue.put(response)
                except json.JSONDecodeError as e:
                    print(f"⚠️  Failed to parse server response: {line}")
                    print(f"   JSON error: {e}")
                    
            except Exception as e:
                if self.running:
                    print(f"⚠️  Error reading from server: {e}")
                break
    
    def send_message(self, message: Dict[str, Any], timeout: float = 5.0) -> Optional[Dict[str, Any]]:
        """
        Send a message to the server and wait for response.
        
        Args:
            message: Message to send
            timeout: Timeout in seconds
            
        Returns:
            Server response or None if timeout/error
        """
        if not self.process or self.process.poll() is not None:
            print("❌ Server is not running")
            return None
            
        # Add ID if not present
        if "id" not in message:
            message["id"] = str(uuid.uuid4())
            
        try:
            # Send message
            message_json = json.dumps(message)
            print(f"📤 Sending: {message_json}")
            self.process.stdin.write(message_json + "\n")
            self.process.stdin.flush()
            
            # Wait for response
            start_time = time.time()
            while time.time() - start_time < timeout:
                try:
                    response = self.response_queue.get(timeout=0.1)
                    print(f"📥 Received: {json.dumps(response, indent=2)}")
                    
                    # Check if this is the response to our message
                    if response.get("id") == message.get("id"):
                        return response
                    else:
                        # Put it back for other handlers
                        self.response_queue.put(response)
                        
                except Empty:
                    continue
                    
            print(f"⏰ Timeout waiting for response to message ID: {message.get('id')}")
            return None
            
        except Exception as e:
            print(f"❌ Error sending message: {e}")
            return None

    def initialize(self) -> bool:
        """
        Initialize the MCP connection.

        Returns:
            True if initialization successful, False otherwise
        """
        print("\n🔄 Initializing MCP connection...")

        # Send initialize message
        init_message = {
            "type": "initialize",
            "params": {
                "protocolVersion": "1.0",
                "clientInfo": {
                    "name": "MCP Test Client",
                    "version": "1.0.0"
                }
            }
        }

        response = self.send_message(init_message)
        if not response or response.get("type") == "error":
            print("❌ Failed to initialize connection")
            return False

        # The initialized message is not needed in this MCP implementation
        # The server responds with initialized message to our initialize request

        self.initialized = True
        print("✅ MCP connection initialized successfully")
        return True

    def ping(self) -> bool:
        """
        Send a ping to test the connection.

        Returns:
            True if ping successful, False otherwise
        """
        print("\n🏓 Sending ping...")

        ping_message = {"type": "ping"}
        response = self.send_message(ping_message)

        if response and response.get("type") == "pong":
            print("✅ Ping successful")
            return True
        else:
            print("❌ Ping failed")
            return False

    def list_tools(self) -> Optional[List[Dict[str, Any]]]:
        """
        List available tools.

        Returns:
            List of tools or None if error
        """
        print("\n🔧 Listing available tools...")

        message = {"type": "list_tools"}
        response = self.send_message(message)

        if response and response.get("type") != "error":
            # The tools are in response.result.tools, not response.tools
            result = response.get("result", {})
            tools = result.get("tools", [])
            print(f"✅ Found {len(tools)} tools:")
            for i, tool in enumerate(tools, 1):
                print(f"  {i}. {tool.get('name', 'Unknown')} - {tool.get('description', 'No description')}")
            return tools
        else:
            print("❌ Failed to list tools")
            return None

    def call_tool(self, tool_name: str, arguments: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        """
        Call a specific tool.

        Args:
            tool_name: Name of the tool to call
            arguments: Arguments to pass to the tool

        Returns:
            Tool response or None if error
        """
        print(f"\n⚙️  Calling tool: {tool_name}")
        if arguments:
            print(f"   Arguments: {arguments}")

        message = {
            "type": "call_tool",
            "params": {
                "name": tool_name,
                "arguments": arguments or {}
            }
        }

        response = self.send_message(message)

        if response and response.get("type") != "error":
            print("✅ Tool call successful")
            return response
        else:
            print("❌ Tool call failed")
            return response

    def list_resources(self) -> Optional[List[Dict[str, Any]]]:
        """
        List available resources.

        Returns:
            List of resources or None if error
        """
        print("\n📚 Listing available resources...")

        message = {"type": "list_resources"}
        response = self.send_message(message)

        if response and response.get("type") != "error":
            # The resources are in response.result.resources
            result = response.get("result", {})
            resources = result.get("resources", [])
            print(f"✅ Found {len(resources)} resources:")
            for i, resource in enumerate(resources, 1):
                print(f"  {i}. {resource.get('id', 'Unknown')} - {resource.get('description', 'No description')}")
            return resources
        else:
            print("❌ Failed to list resources")
            return None

    def read_resource(self, uri: str) -> Optional[Dict[str, Any]]:
        """
        Read a specific resource.

        Args:
            uri: URI of the resource to read

        Returns:
            Resource content or None if error
        """
        print(f"\n📖 Reading resource: {uri}")

        message = {
            "type": "read_resource",
            "params": {"id": uri}
        }

        response = self.send_message(message)

        if response and response.get("type") != "error":
            print("✅ Resource read successful")
            return response
        else:
            print("❌ Failed to read resource")
            return response

    def shutdown(self):
        """Shutdown the client and server."""
        print("\n🛑 Shutting down...")

        self.running = False

        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait()
            except Exception as e:
                print(f"⚠️  Error during shutdown: {e}")

        print("✅ Shutdown complete")


def run_interactive_tests(client: MCPTestClient):
    """Run interactive tests with the MCP server."""

    print("\n" + "="*60)
    print("🧪 MCP INTERACTIVE TEST SUITE")
    print("="*60)

    # Test 1: Ping
    if not client.ping():
        print("❌ Basic connectivity test failed")
        return False

    # Test 2: List tools
    tools = client.list_tools()
    if not tools:
        print("❌ No tools available")
        return False

    # Test 3: Test calculator tool
    print("\n" + "-"*40)
    print("🧮 Testing Calculator Tool")
    print("-"*40)

    calc_tests = [
        {"operation": "add", "a": 15, "b": 27},
        {"operation": "multiply", "a": 6, "b": 7},
        {"operation": "divide", "a": 100, "b": 4},
    ]

    for test in calc_tests:
        result = client.call_tool("calculator", test)
        if result:
            content = result.get("content", [])
            if content and len(content) > 0:
                print(f"   {test['a']} {test['operation']} {test['b']} = {content[0].get('text', 'No result')}")

    # Test 4: Test echo tool
    print("\n" + "-"*40)
    print("🔊 Testing Echo Tool")
    print("-"*40)

    echo_result = client.call_tool("echo", {
        "message": "Hello MCP Test Client!",
        "repeat": 2
    })

    if echo_result:
        content = echo_result.get("content", [])
        if content:
            print(f"   Echo result: {content[0].get('text', 'No result')}")

    # Test 5: Test time tool
    print("\n" + "-"*40)
    print("⏰ Testing Time Tool")
    print("-"*40)

    time_result = client.call_tool("time", {"format": "human"})
    if time_result:
        content = time_result.get("content", [])
        if content:
            print(f"   Current time: {content[0].get('text', 'No result')}")

    # Test 6: List and read resources
    print("\n" + "-"*40)
    print("📚 Testing Resources")
    print("-"*40)

    resources = client.list_resources()
    if resources and len(resources) > 0:
        # Try to read the first resource
        first_resource = resources[0]
        uri = first_resource.get("id")  # Use 'id' field for resource URI
        if uri:
            resource_content = client.read_resource(uri)
            if resource_content:
                result = resource_content.get("result", {})
                content = result.get("content", "")
                if content:
                    preview = content[:200] + "..." if len(content) > 200 else content
                    print(f"   Resource preview: {preview}")

    print("\n✅ All tests completed!")
    return True


def run_custom_test(client: MCPTestClient):
    """Run a custom interactive test session."""

    print("\n" + "="*60)
    print("🎮 CUSTOM TEST MODE")
    print("="*60)
    print("Available commands:")
    print("  ping          - Test connection")
    print("  tools         - List available tools")
    print("  call <tool>   - Call a specific tool")
    print("  resources     - List available resources")
    print("  read <uri>    - Read a specific resource")
    print("  quit          - Exit custom test mode")
    print("-"*60)

    while True:
        try:
            command = input("\n🎯 Enter command: ").strip().lower()

            if command == "quit":
                break
            elif command == "ping":
                client.ping()
            elif command == "tools":
                client.list_tools()
            elif command.startswith("call "):
                tool_name = command[5:].strip()
                if tool_name:
                    print(f"Enter arguments for {tool_name} (JSON format, or press Enter for empty):")
                    args_input = input("Arguments: ").strip()
                    try:
                        args = json.loads(args_input) if args_input else {}
                        client.call_tool(tool_name, args)
                    except json.JSONDecodeError:
                        print("❌ Invalid JSON format for arguments")
                else:
                    print("❌ Please specify a tool name")
            elif command == "resources":
                client.list_resources()
            elif command.startswith("read "):
                uri = command[5:].strip()
                if uri:
                    client.read_resource(uri)
                else:
                    print("❌ Please specify a resource URI")
            else:
                print("❌ Unknown command. Type 'quit' to exit.")

        except KeyboardInterrupt:
            print("\n\n👋 Exiting custom test mode...")
            break
        except Exception as e:
            print(f"❌ Error: {e}")


def main():
    """Main function to run the MCP test client."""

    print("🚀 MCP Test Client")
    print("==================")

    # Parse command line arguments
    import argparse
    parser = argparse.ArgumentParser(description="Test client for MCP Learning Server")
    parser.add_argument("--server-cmd", nargs="+",
                       default=["python", "-m", "mcp_server", "--debug"],
                       help="Command to start the MCP server")
    parser.add_argument("--mode", choices=["auto", "custom"], default="auto",
                       help="Test mode: auto (run predefined tests) or custom (interactive)")

    args = parser.parse_args()

    # Create and start client
    client = MCPTestClient(server_command=args.server_cmd)

    try:
        # Start the server
        if not client.start_server():
            print("❌ Failed to start MCP server")
            return 1

        # Initialize the connection
        if not client.initialize():
            print("❌ Failed to initialize MCP connection")
            return 1

        # Run tests based on mode
        if args.mode == "auto":
            success = run_interactive_tests(client)
            return 0 if success else 1
        else:
            run_custom_test(client)
            return 0

    except KeyboardInterrupt:
        print("\n\n👋 Interrupted by user")
        return 0
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return 1
    finally:
        client.shutdown()


if __name__ == "__main__":
    sys.exit(main())
