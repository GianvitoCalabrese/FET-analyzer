import psutil

def kill_processes_on_port(port):
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            connections = proc.connections()
        except psutil.AccessDenied:
            continue
        for conn in connections:
            if conn.laddr.port == port:
                print(f"Terminating process: {proc.info}")
                proc.terminate()

if __name__ == "__main__":
    port_to_kill = 3000
    kill_processes_on_port(port_to_kill)
