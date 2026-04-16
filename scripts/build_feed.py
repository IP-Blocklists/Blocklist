import socket
import ipaddress

def load_list(file):
    with open(file) as f:
        return [line.strip() for line in f if line.strip()]

def is_ip(value):
    try:
        ipaddress.ip_network(value, strict=False)
        return True
    except:
        return False

# Load inputs
ips_input = load_list("source/ips.txt")
domains = load_list("source/domains.txt")

socket.setdefaulttimeout(2)

# -------------------------
# 1. PROCESS IPS ONLY
# -------------------------
valid_ips = set()

for item in ips_input:
    if is_ip(item):
        valid_ips.add(item)

with open("ip-feed.txt", "w") as f:
    for ip in sorted(valid_ips):
        f.write(ip + "\n")

# -------------------------
# 2. RESOLVE DOMAINS → IPs
# -------------------------
resolved_ips = set()

for domain in domains:
    try:
        result = socket.gethostbyname_ex(domain)
        for ip in result[2]:
            resolved_ips.add(ip)
    except Exception:
        print(f"Failed to resolve {domain}")

with open("fqdn-feed.txt", "w") as f:
    for ip in sorted(resolved_ips):
        f.write(ip + "\n")

print("Feeds generated successfully.")
