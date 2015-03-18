import pickle
import logging
import logging.handlers
import SocketServer
import thread
import struct

# from: https://docs.python.org/2/howto/logging-cookbook.html


class PlungeLogRecordStreamHandler(SocketServer.StreamRequestHandler):
    def handle(self):
        """
        Handle multiple requests - each expected to be a 4-byte length,
        followed by the LogRecord in pickle format. Logs the record
        according to whatever policy is configured locally.
        """
        while True:
            chunk = self.connection.recv(4)
            if len(chunk) < 4:
                break
            slen = struct.unpack('>L', chunk)[0]
            chunk = self.connection.recv(slen)
            while len(chunk) < slen:
                chunk = chunk + self.connection.recv(slen - len(chunk))
            obj = pickle.loads(chunk)
            record = logging.makeLogRecord(obj)
            self.handleLogRecord(record)

    def handleLogRecord(self, record):
        logger = logging.getLogger('Plunge')
        logger.handle(record)

class LogRecordSocketReceiver(SocketServer.ThreadingTCPServer):
    allow_reuse_address = 1
    def __init__(self, host='localhost',
                 port=logging.handlers.DEFAULT_TCP_LOGGING_PORT,
                 handler=PlungeLogRecordStreamHandler):
        SocketServer.ThreadingTCPServer.__init__(self, (host, port), handler)
        self.abort = 0
        self.timeout = 1

    def serve_until_stopped(self):
        import select
        abort = 0
        while not abort:
            rd, wr, ex = select.select([self.socket.fileno()], [], [], self.timeout)
            if rd:
                self.handle_request()
            abort = self.abort

def start_logging_receiver(name):
    tcpserver = LogRecordSocketReceiver()
    thread.start_new_thread(tcpserver.serve_until_stopped, ())
