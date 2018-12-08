from scapy.all import sniff, ifaces, IP, ICMP, hexdump

def generate_icmp_packet(destination_ip, ttl):
    '''
    Layering ICMP packest with supplied IP address and ttl, other parameters go by default
    destination_ip: IP that packet sent to 
    ttl: ttl of packet sent
    '''
    return IP(dst = destination_ip, ttl = ttl)/ICMP()/'your message'

def three_packets():
    '''
    Generate and return packets to UIowa, Google, and UNSW
    No arguments
    '''
    packets_list = []
    packets_list.append(generate_icmp_packet("128.255.96.68", 100)) # generate Uiowa packet
    packets_list.append(generate_icmp_packet("8.8.8.8", 100)) # generate google packet
    packets_list.append(generate_icmp_packet("129.94.124.115", 100)) # generate Sydney packet 
    print('UIowa')
    packets_list[0].show()
    print('Google')
    packets_list[1].show()
    print('UNSW-Sydney')
    packets_list[2].show()
    return packets_list # return a list of packets
packets_list = three_packets()