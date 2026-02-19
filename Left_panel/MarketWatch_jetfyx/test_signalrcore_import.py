try:
    from signalrcore.hub.connection_builder import HubConnectionBuilder
    print("signalrcore.hub.connection_builder import: OK")
except ImportError as e:
    print("signalrcore.hub.connection_builder failed:", e)
    try:
        from signalrcore.connection.hub.connection_builder import HubConnectionBuilder
        print("signalrcore.connection.hub.connection_builder import: OK")
    except ImportError as e2:
        print("signalrcore.connection.hub.connection_builder failed:", e2)
