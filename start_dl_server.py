from Instruments.delay_line_mercury import dl

if __name__ == '__main__':
    import xmlrpc.server

    server = xmlrpc.server.SimpleXMLRPCServer(('',8000))
    server.register_instance(dl)
    server.serve_forever()