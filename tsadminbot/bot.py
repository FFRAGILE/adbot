import socket
import time
import re
import threading

class TS3Bot:
    def __init__(self, host, port, vport, user, password, name, supports, admins):
        self.host = host
        self.port = port
        self.vport = vport
        self.user = user
        self.password = password
        self.name = name
        self.supports = supports
        self.admins = admins
        
        self.s = None
        self.lock = threading.Lock() # Thread safety lock for socket
        self.running = True
        self.users_in_support = set()

    def send(self, cmd):
        """Sends a command safely using thread locking and returns response."""
        with self.lock:
            if not self.s:
                return ""
            if cmd:
                try:
                    self.s.sendall((cmd + "\n").encode('utf-8'))
                except Exception:
                    return ""
                time.sleep(0.1)
            
            res = ""
            try:
                while True:
                    chunk = self.s.recv(8192).decode('utf-8', errors='ignore')
                    if not chunk:
                        break
                    res += chunk
                    if "error id=" in chunk:
                        break
            except Exception:
                pass
            return res

    def connect(self):
        """Attempts to connect, login, and configure the bot query session."""
        while self.running:
            try:
                print(f"[!] Connecting to query port {self.port}...")
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(4)
                s.connect((self.host, self.port))
                
                # Assign to class variable within lock
                with self.lock:
                    self.s = s
                
                # Initialize connection
                self.send("")
                login_res = self.send(f"login {self.user} {self.password}")
                use_res = self.send(f"use port={self.vport}")
                nick_res = self.send(f"clientupdate client_nickname={self.name}")
                
                if "error id=0" in login_res and "error id=0" in use_res:
                    print(f"[+] Successfully connected & logged in as '{self.name}' on port {self.vport}.\n")
                    return True
                else:
                    print("[-] Authentication or Virtual Port selection failed! Check credentials.")
                    time.sleep(3)
            except Exception as e:
                print(f"[!] Connection failed: {e}. Retrying in 3 seconds...")
                time.sleep(3)

    def get_online_admins(self):
        """Retrieves currently online admins in a single request."""
        admin_clids = set()
        raw_clients = self.send("clientlist -groups")
        if "clid=" not in raw_clients:
            return []

        clients = raw_clients.split('|')
        for c in clients:
            clid_m = re.search(r'\bclid=(\d+)', c)
            groups_m = re.search(r'client_servergroups=([0-9,]+)', c)
            type_m = re.search(r'client_type=(\d+)', c)
            
            if clid_m and groups_m:
                clid = clid_m.group(1)
                groups = [int(x) for x in groups_m.group(1).split(',') if x.isdigit()]
                ctype = type_m.group(1) if type_m else "0"
                
                if ctype == "0" and any(a in groups for a in self.admins):
                    admin_clids.add(clid)
                        
        return list(admin_clids)

    def monitor(self):
        """Background loop to monitor support channels and notify admins."""
        while self.running:
            try:
                raw_clients = self.send("clientlist")
                if not raw_clients or "error id=0" not in raw_clients:
                    print("\n[!] Connection lost in monitor thread. Attempting reconnect...")
                    self.connect()
                    continue

                current_support_users = set()
                clients = raw_clients.split('|')
                for c in clients:
                    cid_m = re.search(r'\bcid=(\d+)', c)
                    clid_m = re.search(r'\bclid=(\d+)', c)
                    nick_m = re.search(r'client_nickname=([^\s]+)', c)
                    type_m = re.search(r'client_type=(\d+)', c)

                    if cid_m and clid_m:
                        cid = int(cid_m.group(1))
                        clid = clid_m.group(1)
                        nick = nick_m.group(1) if nick_m else "User"
                        ctype = type_m.group(1) if type_m else "0"

                        if cid in self.supports and ctype == "0":
                            current_support_users.add((clid, nick, cid))

                for clid, nick, cid in current_support_users:
                    if clid not in self.users_in_support:
                        print(f"\n[*] NOTIFICATION: '{nick}' entered support channel {cid}.")
                        admins = self.get_online_admins()
                        print(f"[*] Online Admins detected: {admins}")
                        
                        if admins:
                            clean_nick = re.sub(r'[^\w]', '', nick) or "User"
                            msg = f"User_{clean_nick}_Entered_Support"
                            for adm_clid in admins:
                                self.send(f"clientpoke clid={adm_clid} msg={msg}")
                                print(f"[>] Poke sent to Admin (CLID: {adm_clid})")
                                time.sleep(0.3)
                        else:
                            print("[-] No online admins found to poke.")

                self.users_in_support = {u[0] for u in current_support_users}

            except Exception as e:
                print(f"\n[!] Error in monitor loop: {e}")
                self.connect()

            time.sleep(2)

    def start_monitoring(self):
        """Starts the background monitoring thread."""
        t = threading.Thread(target=self.monitor, daemon=True)
        t.start()

    def cli(self):
        """Main thread loop for interactive CMD console."""
        print("=" * 50)
        print("           TS3 BOT CONSOLE STARTED")
        print(" You can execute any standard ServerQuery commands.")
        print(" Special Commands:")
        print("   help   - Show helper guide")
        print("   status - Check bot connection & configs")
        print("   exit   - Shut down the bot completely")
        print("=" * 50 + "\n")

        while self.running:
            try:
                cmd = input("Bot Console> ").strip()
                if not cmd:
                    continue

                if cmd.lower() == "exit":
                    print("[!] Shutting down bot session...")
                    self.running = False
                    break
                elif cmd.lower() == "help":
                    print("\n[Help Menu]")
                    print("  exit    : Terminates the bot.")
                    print("  status  : Prints server connection info.")
                    print("  help    : Shows this menu.")
                    print("  Or enter raw TS3 Query commands (e.g. 'clientlist', 'serverinfo', etc.)\n")
                elif cmd.lower() == "status":
                    print(f"\n[Status: Active]")
                    print(f"  Host: {self.host}:{self.port} (Virtual Voice Port: {self.vport})")
                    print(f"  Bot Nickname: {self.name}")
                    print(f"  Target Support Channels: {self.supports}")
                    print(f"  Admin ServerGroups: {self.admins}\n")
                else:
                    # Execute raw TeamSpeak Query command entered by user
                    response = self.send(cmd)
                    if response:
                        print(response.strip())
                    else:
                        print("[-] Failed to execute or empty response from server.")
            except (KeyboardInterrupt, EOFError):
                print("\n[!] Exiting safely...")
                self.running = False
                break
            except Exception as e:
                print(f"[-] Console error: {e}")

        # Cleanup socket on exit
        with self.lock:
            if self.s:
                try:
                    self.s.close()
                except Exception:
                    pass


def main():
    print("==================================================")
    print("        WELCOME TO TS3 SUPPORT BOT CONFIG")
    print("  Press Enter to accept the [Default] values.")
    print("==================================================")
    
    host = input("Server IP [62.220.120.120]: ").strip() or "62.220.120.120"
    
    port_input = input("Query Port [5023]: ").strip()
    port = int(port_input) if port_input else 5023
    
    vport_input = input("Voice Port [4023]: ").strip()
    vport = int(vport_input) if vport_input else 4023
    
    user = input("Query Username [BOT]: ").strip() or "BOT"
    password = input("Query Password [uhV6tCbFrqtx.]: ").strip() or "uhV6tCbFrqtx."
    bot_name = input("Bot Nickname [Support-Bot]: ").strip() or "Support-Bot"
    
    supports_input = input("Support Channel IDs (comma separated) [79,80,81]: ").strip()
    supports = [int(x.strip()) for x in supports_input.split(",") if x.strip().isdigit()] if supports_input else [79, 80, 81]
    
    admins_input = input("Admin ServerGroup IDs (comma separated) [25,19]: ").strip()
    admins = [int(x.strip()) for x in admins_input.split(",") if x.strip().isdigit()] if admins_input else [25, 19]
    print()

    # Create and run the bot
    bot = TS3Bot(host, port, vport, user, password, bot_name, supports, admins)
    if bot.connect():
        bot.start_monitoring() # Background support monitoring thread
        bot.cli()              # Main interactive console thread

if __name__ == "__main__":
    main()
