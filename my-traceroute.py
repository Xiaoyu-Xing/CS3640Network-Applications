from scapy.all import sr
from craft_a_packet import generate_icmp_packet

def send_and_receive_packets(packets_to_send):
    '''
    send packets and receive answers, abandon unanswered
    packets_to_send: a list of packets to be sent
    '''
    responses = []
    for packet in packets_to_send: # loop each packet in the list and send them, then receive answers
        answer, unanswer = sr(packet, timeout = 10)
        responses.append(answer)
    return responses

def get_all_hops(destination_ip):
    '''
    Parse in dest ip, send packet based on decreasing ttl from 10 to 1.
    Print answered packet ttl and source ip, no display for unanswered ip.
    For the time that we ran the code on campus, only ttl = 10, 9, 8, 1 was answered.
    Several deviding line for testing purpose, the code for the lines was deleted, but the code was not ran again after that.
    '''
    ttl = 10
    packets = {}
    while ttl >= 1: # send packets and store answered packet list in a dictionary with ttl as key
        packet = generate_icmp_packet(destination_ip, ttl)
        response = send_and_receive_packets(packet)
        packets[ttl] = response   
        ttl = ttl - 1
    for i in range(10, 0, -1): # loop through to show source IP for each ttl, unanswered packets for that ttl was ignored
        try:
            print(f'TTL value: {i} | Source IP in response: {packets[i][0][0][1].src}')
#             the indexing here is to first get ttl corresponding response list from dictionary, 
# second indexing is to get the first item from the response list, then get the ip src from the packet
        except:
            continue
    return packets
get_all_hops('8.8.8.8')