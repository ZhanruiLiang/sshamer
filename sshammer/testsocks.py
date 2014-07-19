from socksclient import Client

def main():
    while 1:
        client = Client(7070)
        print(client.connect('google.com', 80))
        client.sock.send('GET /\n'.encode())
        print(client._rfile.readline().decode())
        client.sock.close()

if __name__ == '__main__':
    main()
