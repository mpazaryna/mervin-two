"""
Stdio Transport Layer for MCP Server

This module implements the stdio-based transport layer for communication
between the MCP server and clients according to the MCP specification.
"""

import sys
import json
import signal
import threading
from typing import Callable, Optional, Dict, Any
from queue import Queue, Empty
import time

from .logging_config import get_logger


class StdioTransport:
    """
    Stdio-based transport layer for MCP communication.

    Handles JSON message reading from stdin and writing to stdout,
    with proper message framing and error handling.
    """

    def __init__(self, message_handler: Callable[[Dict[str, Any]], Dict[str, Any]]):
        """
        Initialize the stdio transport.

        Args:
            message_handler: Function to handle incoming messages
        """
        self.message_handler = message_handler
        self.logger = get_logger("stdio_transport")

        # Transport state
        self.running = False
        self.shutdown_requested = False

        # Message queues for buffering
        self.input_queue = Queue()
        self.output_queue = Queue()

        # Threads for I/O operations
        self.input_thread: Optional[threading.Thread] = None
        self.output_thread: Optional[threading.Thread] = None
        self.processor_thread: Optional[threading.Thread] = None

        # Setup signal handlers for graceful shutdown
        self._setup_signal_handlers()

        self.logger.info("Stdio transport initialized")

    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown."""
        def signal_handler(signum, frame):
            self.logger.info(f"Received signal {signum}, initiating shutdown")
            self.shutdown()

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

    def start(self):
        """Start the transport layer."""
        if self.running:
            self.logger.warning("Transport already running")
            return

        self.logger.info("Starting stdio transport")
        self.running = True
        self.shutdown_requested = False

        # Start I/O threads
        self.input_thread = threading.Thread(target=self._input_loop, daemon=True)
        self.output_thread = threading.Thread(target=self._output_loop, daemon=True)
        self.processor_thread = threading.Thread(target=self._processor_loop, daemon=True)

        self.input_thread.start()
        self.output_thread.start()
        self.processor_thread.start()

        self.logger.info("Stdio transport started")

        # Main loop - wait for shutdown
        try:
            while self.running and not self.shutdown_requested:
                time.sleep(0.1)
        except KeyboardInterrupt:
            self.logger.info("Keyboard interrupt received")
        finally:
            self.shutdown()

    def shutdown(self):
        """Shutdown the transport layer gracefully."""
        if not self.running:
            return

        self.logger.info("Shutting down stdio transport")
        self.shutdown_requested = True
        self.running = False

        # Wait for threads to finish (with timeout)
        threads = [self.input_thread, self.output_thread, self.processor_thread]
        for thread in threads:
            if thread and thread.is_alive():
                thread.join(timeout=1.0)

        self.logger.info("Stdio transport shutdown complete")

    def _input_loop(self):
        """Input loop - reads messages from stdin."""
        self.logger.debug("Input loop started")

        try:
            while self.running and not self.shutdown_requested:
                try:
                    # Read line from stdin
                    line = sys.stdin.readline()

                    # Check for EOF
                    if not line:
                        self.logger.info("EOF received on stdin")
                        break

                    # Strip whitespace
                    line = line.strip()
                    if not line:
                        continue

                    # Add to input queue
                    self.input_queue.put(line)
                    self.logger.debug(f"Queued input message: {line[:100]}...")

                except Exception as e:
                    self.logger.error(f"Error reading from stdin: {e}")
                    break

        except Exception as e:
            self.logger.error(f"Fatal error in input loop: {e}")
        finally:
            self.logger.debug("Input loop ended")

    def _output_loop(self):
        """Output loop - writes messages to stdout."""
        self.logger.debug("Output loop started")

        try:
            while self.running and not self.shutdown_requested:
                try:
                    # Get message from output queue (with timeout)
                    try:
                        message = self.output_queue.get(timeout=0.1)
                    except Empty:
                        continue

                    # Write to stdout
                    sys.stdout.write(message + '\n')
                    sys.stdout.flush()

                    self.logger.debug(f"Sent output message: {message[:100]}...")

                except Exception as e:
                    self.logger.error(f"Error writing to stdout: {e}")
                    break

        except Exception as e:
            self.logger.error(f"Fatal error in output loop: {e}")
        finally:
            self.logger.debug("Output loop ended")

    def _processor_loop(self):
        """Message processor loop - handles incoming messages."""
        self.logger.debug("Processor loop started")

        try:
            while self.running and not self.shutdown_requested:
                try:
                    # Get message from input queue (with timeout)
                    try:
                        raw_message = self.input_queue.get(timeout=0.1)
                    except Empty:
                        continue

                    # Process the message
                    self._process_message(raw_message)

                except Exception as e:
                    self.logger.error(f"Error in processor loop: {e}")
                    # Continue processing other messages

        except Exception as e:
            self.logger.error(f"Fatal error in processor loop: {e}")
        finally:
            self.logger.debug("Processor loop ended")

    def _process_message(self, raw_message: str):
        """
        Process a single message.

        Args:
            raw_message: Raw JSON message string
        """
        try:
            # Parse JSON
            message_data = json.loads(raw_message)
            self.logger.debug(f"Processing message: {message_data.get('type', 'unknown')}")

            # Handle the message
            response_data = self.message_handler(message_data)

            # Convert response to JSON
            response_json = json.dumps(response_data, separators=(',', ':'))

            # Queue response for output
            self.output_queue.put(response_json)

        except json.JSONDecodeError as e:
            self.logger.error(f"JSON decode error: {e}")
            # Send error response
            error_response = {
                "type": "error",
                "error": f"Invalid JSON: {str(e)}",
                "code": 400
            }
            error_json = json.dumps(error_response, separators=(',', ':'))
            self.output_queue.put(error_json)

        except Exception as e:
            self.logger.error(f"Error processing message: {e}")
            # Send error response
            error_response = {
                "type": "error",
                "error": f"Processing error: {str(e)}",
                "code": 500
            }
            error_json = json.dumps(error_response, separators=(',', ':'))
            self.output_queue.put(error_json)

    def send_message(self, message: Dict[str, Any]):
        """
        Send a message (for testing or notifications).

        Args:
            message: Message dictionary to send
        """
        try:
            message_json = json.dumps(message, separators=(',', ':'))
            self.output_queue.put(message_json)
            self.logger.debug(f"Queued outgoing message: {message.get('type', 'unknown')}")
        except Exception as e:
            self.logger.error(f"Error queuing message: {e}")

    def is_running(self) -> bool:
        """Check if transport is running."""
        return self.running and not self.shutdown_requested

    def get_stats(self) -> Dict[str, Any]:
        """Get transport statistics."""
        return {
            "running": self.running,
            "shutdown_requested": self.shutdown_requested,
            "input_queue_size": self.input_queue.qsize(),
            "output_queue_size": self.output_queue.qsize(),
            "threads_alive": {
                "input": self.input_thread.is_alive() if self.input_thread else False,
                "output": self.output_thread.is_alive() if self.output_thread else False,
                "processor": self.processor_thread.is_alive() if self.processor_thread else False
            }
        }


class SimpleStdioTransport:
    """
    Simple stdio transport for basic use cases.

    This is a simpler, synchronous version of the stdio transport
    that can be used for testing or simple applications.
    """

    def __init__(self, message_handler: Callable[[Dict[str, Any]], Dict[str, Any]]):
        """
        Initialize the simple stdio transport.

        Args:
            message_handler: Function to handle incoming messages
        """
        self.message_handler = message_handler
        self.logger = get_logger("simple_stdio_transport")
        self.running = False

        self.logger.info("Simple stdio transport initialized")

    def start(self):
        """Start the simple transport layer."""
        self.logger.info("Starting simple stdio transport")
        self.running = True

        try:
            while self.running:
                try:
                    # Read message from stdin
                    line = sys.stdin.readline()
                    if not line:
                        self.logger.info("EOF received, stopping transport")
                        break

                    # Strip whitespace
                    line = line.strip()
                    if not line:
                        continue

                    # Parse JSON message
                    message_data = json.loads(line)
                    self.logger.debug(f"Received message: {message_data.get('type', 'unknown')}")

                    # Process message and get response
                    response_data = self.message_handler(message_data)

                    # Write response to stdout
                    response_json = json.dumps(response_data, separators=(',', ':'))
                    sys.stdout.write(response_json + '\n')
                    sys.stdout.flush()

                    self.logger.debug(f"Sent response: {response_data.get('type', 'unknown')}")

                except json.JSONDecodeError as e:
                    self.logger.error(f"JSON decode error: {e}")
                    error_response = {
                        "type": "error",
                        "error": f"Invalid JSON: {str(e)}",
                        "code": 400
                    }
                    error_json = json.dumps(error_response, separators=(',', ':'))
                    sys.stdout.write(error_json + '\n')
                    sys.stdout.flush()

                except KeyboardInterrupt:
                    self.logger.info("Keyboard interrupt received")
                    break

                except Exception as e:
                    self.logger.error(f"Error processing message: {e}")
                    error_response = {
                        "type": "error",
                        "error": f"Processing error: {str(e)}",
                        "code": 500
                    }
                    error_json = json.dumps(error_response, separators=(',', ':'))
                    sys.stdout.write(error_json + '\n')
                    sys.stdout.flush()

        finally:
            self.running = False
            self.logger.info("Simple stdio transport stopped")

    def stop(self):
        """Stop the transport."""
        self.running = False
