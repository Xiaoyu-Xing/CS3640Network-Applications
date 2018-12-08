from scapy.all import sniff, ifaces

print (ifaces) # choose your internet interface here

def find_packets_to_hosts(interface, host_ips, max_count):
    '''
    Sniff the max_count number of packets from a interface, and 
    determine whether IP from or to in these packets match anyone in a list of host IPS,
    then return a list of packets found
    
    Arguments:
    interface: interface monitored
    host_ips: ip to be checked in a packet
    max_count: max number of packets monitored
    '''
    pks = sniff(iface = interface, count = max_count)
    packest_list = []
    for packet in pks:
        if 'IP' in packet: #find out whether its IPv4
            ip_dst = packet['IP'].dst
            ip_src = packet['IP'].src
        elif 'IPv6' in packet: #find out whether its IPv6
            ip_dst = packet['IPv6'].dst
            ip_src = packet['IPv6'].src
        else:
            continue
        if ip_dst in host_ips or ip_src in host_ips: # find match ip
            packest_list.append(packet)
    return packest_list

host_ips=["YOUR MONITORED IP ADDRESS HERE"]
output = find_packets_to_hosts('YOUR INTERNET INTERFACE HERE', host_ips, 10**3)
for i, packet in enumerate(output):
    print(f'Packet #{i}') 
    print(f'Link layer: {packet["Ethernet"].src} (src link address) -> {packet["Ethernet"].dst} (dst link address)')
    if 'IP' in packet: # get the IPv4 info
        print(f'Network layer: {packet["IP"].src} (src IPv4 address) -> {packet["IP"].dst} (dst IPv4 address)')
    else: # get IPv6 info
        print(f'Network layer: {packet["IPv6"].src} (src IPv6 address) -> {packet["IPv6"].dst} (dst IPv6 address)')
    print(f'Transport layer: {packet["TCP"].sport} (src port) -> {packet["TCP"].dport} (dst port)') # get transport layer info