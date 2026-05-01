import ipaddress
import dns.resolver
from concurrent.futures import ThreadPoolExecutor, as_completed

DNS_SERVERS = None
# Optional custom DNS:
# DNS_SERVERS = ["1.1.1.1", "8.8.8.8"]

MAX_WORKERS = 20
DNS_TIMEOUT = 3


def load_list(file):
    with open(file) as f:
        return [
            line.strip()
            for line in f
            if line.strip() and not line.strip().startswith("#")
        ]


def is_ip(value):
    try:
        ipaddress.ip_network(value, strict=False)
        return True
    except ValueError:
        return False


def is_public_ip(value):
    try:
        ip = ipaddress.ip_address(value)
        return not (
            ip.is_private
            or ip.is_loopback
            or ip.is_multicast
            or ip.is_reserved
            or ip.is_link_local
        )
    except ValueError:
        return False


def make_resolver():
    resolver = dns.resolver.Resolver()
    resolver.timeout = DNS_TIMEOUT
    resolver.lifetime = DNS_TIMEOUT

    if DNS_SERVERS:
        resolver.nameservers = DNS_SERVERS

    return resolver


def resolve_domain(domain):
    resolver = make_resolver()
    found_ips = set()
    cname_chain = []

    try:
        current = domain.rstrip(".")

        # Follow CNAME chain up to 10 hops
        for _ in range(10):
            try:
                cname_answers = resolver.resolve(current, "CNAME")
                cname = str(cname_answers[0].target).rstrip(".")
                cname_chain.append(f"{current} -> {cname}")
                current = cname
            except dns.resolver.NoAnswer:
                break
            except dns.resolver.NXDOMAIN:
                print(f"NXDOMAIN: {domain}")
                return set()
            except Exception:
                break

        # Resolve IPv4 A records
        try:
            answers = resolver.resolve(current, "A")
            for rdata in answers:
                ip = rdata.to_text()
                if is_public_ip(ip):
                    found_ips.add(ip)
        except Exception:
            pass

        # Optional IPv6 AAAA records
        # Uncomment if you want IPv6 in the feed
        # try:
        #     answers = resolver.resolve(current, "AAAA")
        #     for rdata in answers:
        #         ip = rdata.to_text()
        #         if is_public_ip(ip):
        #             found_ips.add(ip)
        # except Exception:
        #     pass

        if cname_chain:
            print(f"CNAME chain for {domain}: {' | '.join(cname_chain)}")

        if not found_ips:
            print(f"No public IPs found for {domain}")

        return found_ips

    except Exception as e:
        print(f"Failed to resolve {domain}: {e}")
        return set()


# -------------------------
# Load inputs
# -------------------------
ips_input = load_list("source/ips.txt")
domains = load_list("source/domains.txt")


# -------------------------
# 1. PROCESS IPS ONLY
# -------------------------
valid_ips = set()

for item in ips_input:
    if is_ip(item):
        valid_ips.add(item)
    else:
        print(f"Invalid IP skipped: {item}")

with open("ip-feed.txt", "w") as f:
    for ip in sorted(valid_ips):
        f.write(ip + "\n")


# -------------------------
# 2. RESOLVE DOMAINS → IPs
# -------------------------
resolved_ips = set()

with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
    futures = {
        executor.submit(resolve_domain, domain): domain
        for domain in domains
        if not domain.startswith("*.")
    }

    for future in as_completed(futures):
        domain = futures[future]
        try:
            resolved_ips.update(future.result())
        except Exception as e:
            print(f"Failed processing {domain}: {e}")


# Log wildcard domains but do not resolve them
for domain in domains:
    if domain.startswith("*."):
        print(f"Wildcard skipped, cannot DNS-resolve directly: {domain}")


with open("fqdn-feed.txt", "w") as f:
    for ip in sorted(resolved_ips):
        f.write(ip + "\n")


print("Feeds generated successfully.")
