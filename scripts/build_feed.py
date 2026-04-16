import socket
import ipaddress

def load_list(file):
    with open(file) as f:
        return [line.strip() for line in f if line.strip()]

def is_ip(value):
    try:
        ipaddress.ip_network(value)
        return True
    except:
        return False

domains = load_list("source/domains.txt")
raw_ips = load_list("source/ips.txt")

resolved_ips = set()

# Resolve domains
for domain in domains:
    try:
        result = socket.gethostbyname_ex(domain)
        for ip in result[2]:
            resolved_ips.add(ip)
    except:
        print(f"Failed to resolve {domain}")

# Validate and collect IPs
all_ips = set()

for ip in raw_ips:
    if is_ip(ip):
        all_ips.add(ip)

all_ips.update(resolved_ips)

# Write outputs
with open("output/ip-feed.txt", "w") as f:
    for ip in sorted(all_ips):
        f.write(ip + "\n")

with open("output/fqdn-feed.txt", "w") as f:
    for d in sorted(set(domains)):
        f.write(d + "\n")
