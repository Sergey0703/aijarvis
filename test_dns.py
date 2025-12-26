import socket

hosts = [
    "cluster0-shard-00-00.llssu.mongodb.net",
    "cluster0.llssu.mongodb.net",
    "google.com"
]

for host in hosts:
    try:
        ip = socket.gethostbyname(host)
        print(f"{host}: {ip}")
    except Exception as e:
        print(f"{host}: Error: {e}")
