import mcstatus

class Server:
    def __init__(self, ip, port, name, type = 'je', method = 'ping'):
        self.ip = ip
        self.port = port
        self.name = name
        self.server = mcstatus.JavaServer(ip, port, timeout=2) if type == 'je' else mcstatus.BedrockServer(ip, port, timeout=2)
        self.status = None
        self.players = None
        self.query = None
        self.fetch_query() if method == 'query' and type == 'je' else self.ping()

    def ping(self):
        try:
            self.status = self.server.status()
            self.players = self.status.players.sample
            return self.status
        except Exception as e:
            self.status = None
            self.players = None
            raise e
        
    def fetch_query(self):
        try:
            self.query = self.server.query()
            self.players = self.query.players.names
            return self.query
        except Exception as e:
            self.query = None
            self.players = None
            raise e

    def get_status(self):
        if self.status:
            return {
                'ip': self.ip,
                'port': self.port,
                'name': self.name,
                'version': self.status.version.name,
                'description': self.status.description['text'],
                'players': self.status.players.online,
                'max_players': self.status.players.max,
                'latency': self.status.latency,
            }
        else:
            return {
                'ip': self.ip,
                'port': self.port,
                'name': self.name,
                'error': '无法连接到服务器。',
            }
    