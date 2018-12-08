from pybgpdump import BGPDump
from dpkt import bgp
import ipaddr
import socket
import time
import sys
from collections import defaultdict
import struct

class ParseUpdates:
    """ParseUpdates will handle all functions related to parsing an MRT file
    
    Attributes:
        filename (str): The name of the file that this ParseUpdate object is handling.
        announcements (dict of lists): Keyed by the MRT header timestamp. 
                                       Contains list of all route announcements received at given timestamp.
        withdrawals (dict of lists): Keyed by the MRT header timestamp.
                                     Contains list of all route withdrawals received at given timestamp.
        n_announcements (int): The number of routes announced by BGP messages in this MRT file.
        n_withdrawals (int): The number of routes withdrawn by BGP messages in this MRT file.
        time_to_parse (int): The time taken to parse the updates contained in this MRT file.
        start_time (int): The timestamp of the first update seen in this file.
        end_time (int): The timestamp of the last update seen in this file.
    Credit of the logic and templates to Rishab
    """
    
    def __init__(self, filename):
        self.filename = filename
        self.announcements, self.withdrawals = {}, {}
        self.n_announcements, self.n_withdrawals = 0, 0
        self.time_to_parse, self.start_time, self.end_time = 0, 0, 0
        
    def parse_updates(self):
        return
    
    def __parse_announcement_update(self, mrt_header, bgp_header, bgp_message, announcement):
        self.n_announcements += 1
        return
    
    def __parse_withdrawal_update(self, mrt_header, bgp_header, bgp_message, announcement):
        self.n_withdrawals += 1
        return
        
    def get_next_updates(self):
        return


class ParseUpdates(ParseUpdates):

    def parse_updates(self):
        """
        Opening and iterating through an MRT file
        mrt_header: This is the header of the MRT record containing the route announcement.
        bgp_header: This is the header of the BGP message containing the route announcement.
        bgp_message: This is the BGP message containing the route announcement.
        announcement: This is the actual announcement in the BGP message.
        """
        dumpfile=BGPDump(self.filename)
        self.start_time=time.time()
        for mrt_header, bgp_header, bgp_message in dumpfile:
            for route in bgp_message.update.announced:
                self.__parse_announcement_update(mrt_header, bgp_header, bgp_message, route)
            for route in bgp_message.update.withdrawn:
                self.__parse_withdrawal_update(mrt_header, bgp_header, bgp_message, route)
        self.end_time=time.time()
        self.time_to_parse=self.end_time-self.start_time
        return True


class ParseUpdates(ParseUpdates):

    def __parse_announcement_update(self, mrt_header, bgp_header, bgp_message, announcement):
            '''
            Parsing announcement updates
            '''
        try:
            if mrt_header.ts not in self.announcements:
                self.announcements[mrt_header.ts]=[]
            update=dict.fromkeys(['timestamp', 'destination_block', 'next_hop', 'source_as', 'as_path'], '')
            timestamp=''
            destination_block='' # CIDR IP address block being updated by the BGP message
            next_hop='' #  IP address of the next hop router
            source_as='' # source AS of the BGP message
            as_path='' # AS path advertised
            self.n_announcements +=1
            for attr in bgp_message.update.attributes:
                if attr.type == bgp.AS_PATH:
                    as_path=self.aspath_to_str(attr.as_path)
                elif attr.type == bgp.NEXT_HOP:
                    next_hop=socket.inet_ntoa(struct.pack('!L',attr.next_hop.ip))
            update['timestamp']=mrt_header.ts
            update['source_as']=bgp_header.src_as
            update['next_hop']=next_hop
            update['as_path']=as_path
            update['destination_block']=str(socket.inet_ntoa(announcement.prefix))+'/'+str(announcement.len)

            self.announcements[mrt_header.ts].append(update)
        except Exception as e:
            print(e)
            return False
        return True
    
    def aspath_to_str(self, as_path):
        str = ''
        for seg in as_path.segments:
            if seg.type == bgp.AS_SET:
                start = '['
                end = '] '
            elif seg.type == bgp.AS_SEQUENCE:
                start = ''
                end = ' '
            else:
                start = '?%d?' % (seg.type)
                end = '? '
            str += start
            for AS in seg.path:
                str += '%d ' % (AS)
            str = str[:-1]
            str += end
        str = str[:-1]
        return str

class ParseUpdates(ParseUpdates):
    def __parse_withdrawal_update(self, mrt_header, bgp_header, bgp_message, withdrawal):
        """
        Parsing withdrawal updates
        mrt_header: This is the header of the MRT record containing the route withdrawal.
        bgp_header: This is the header of the BGP message containing the route withdrawal.
        bgp_message: This is the BGP message containing the route withdrawal.
        withdrawal: This is the actual withdrawal in the BGP message.
        """
        try: 
            if mrt_header.ts not in self.withdrawals:
                self.withdrawals[mrt_header.ts]=[]
            update=dict.fromkeys(['timestamp', 'destination_block', 'source_as'], '')
            timestamp=''
            destination_block=''
            source_as=''
            self.n_withdrawals +=1
            update['timestamp']=mrt_header.ts
            update['source_as']=bgp_header.src_as
            update['destination_block']=socket.inet_ntoa(withdrawal.prefix)+'/'+str(withdrawal.len)
            self.withdrawals[mrt_header.ts].append(update)
        except Exception as e:
            print(e)
            return False
        return True

class ParseUpdates(ParseUpdates):
    def get_next_updates(self):
        '''
        Streaming BGP updates
        '''
        timestamp=min(self.announcements.keys())
        timestampmax=max(self.announcements.keys())
        while(timestamp<=timestampmax):
            try:
                yield {"timestamp": timestamp, "announcements": self.announcements.get(timestamp), "withdrawals":self.withdrawals.get(timestamp)}
                timestamp=timestamp+1
            except Exception as e:
                print(e)
                yield {"timestamp": None, "announcements": None, "withdrawals":None}
        yield {"timestamp": None, "announcements": None, "withdrawals":None}