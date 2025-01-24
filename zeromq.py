import asyncio
import zmq
import zmq.asyncio

class ZeroMQManager:
    _instances = {}

    def __new__(cls, role, address, port):
        """
        Implement the Singleton pattern.

        :param role: 'server' or 'client'
        :param address: IP address or hostname
        :param port: Port number
        """
        key = (role, address, port)
        if key not in cls._instances:
            instance = super(ZeroMQManager, cls).__new__(cls)
            cls._instances[key] = instance
        return cls._instances[key]

    def __init__(self, role, address, port):
        if not hasattr(self, "initialized"):
            self.role = role
            self.address = address
            self.port = port
            self.context = zmq.asyncio.Context()
            self.socket = None

            if self.role == "server":
                self.socket = self.context.socket(zmq.REP)
                self.socket.bind(f"tcp://{self.address}:{self.port}")
            elif self.role == "client":
                self.socket = self.context.socket(zmq.REQ)
                self.socket.connect(f"tcp://{self.address}:{self.port}")
            else:
                raise ValueError("Role must be 'server' or 'client'")

            self.initialized = True

    async def send(self, message):
        """
        Send a message (client-only).

        :param message: The message to send
        """
        if self.role != "client":
            raise RuntimeError("Send method can only be used by the client")
        await self.socket.send(message.encode("utf-8"))

    async def receive(self):
        """
        Receive a message (blocking).

        :return: The received message as a string
        """
        message = await self.socket.recv()
        return message.decode("utf-8")

    async def reply(self, message):
        """
        Reply to a received message (server-only).

        :param message: The reply to send
        """
        if self.role != "server":
            raise RuntimeError("Reply method can only be used by the server")
        await self.socket.send(message.encode("utf-8"))

    def close(self):
        """Clean up the socket and context."""
        self.socket.close()
        self.context.term()



# Example usage
if __name__ == "__main__":
    async def server_task():
        server = ZeroMQManager("server", "*", 5555)
        print("Server is running...")
        try:
            while True:
                message = await server.receive()
                print(f"Server received: {message}")
                await asyncio.sleep(1)  # Simulate work
                await server.reply("World")
        except asyncio.CancelledError:
            pass
        finally:
            server.close()

    async def client_task():
        client = ZeroMQManager("client", "localhost", 5555)
        try:
            for i in range(10):
                print(f"Client sending: Hello {i}")
                await client.send("Hello")
                reply = await client.receive()
                print(f"Client received: {reply}")
        finally:
            client.close()

    async def main():
        server = asyncio.create_task(server_task())
        await asyncio.sleep(1)  # Give the server a moment to start
        client = asyncio.create_task(client_task())

        await asyncio.gather(server, client)

    asyncio.run(main())
