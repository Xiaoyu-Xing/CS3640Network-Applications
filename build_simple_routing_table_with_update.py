from pybgpdump import BGPDump
from dpkt import bgp
import ipaddr
import socket
import time
import sys
from collections import defaultdict
import struct
import glob

class RoutingTable:
    """RoutingTable will handle all functions related to handling simplified BGP update messages.
    
    Attributes:
        routing_table (dict): All the entries in the routing table. Keyed by CIDR destination block.
        time_of_earliest_update (int): The timestamp of the first update seen by this routing table.
        time_of_latest_update (int): The timestamp of the last update seen by this routing table.
        total_updates_received (int): The total number of BGP updates ever seen by this routing table.
        total_paths_changed (int): The total number of paths to a destination that have been modified by an update.
    credit to Rishan for the templates
    """
    def __init__(self):
        self.routing_table = {}
        self.time_of_earliest_update, self.time_of_latest_update = sys.maxint, 0
        self.total_updates_received = 0
        self.total_paths_changed = 0

    def apply_announcement(self, update):
        return
    
    def apply_withdrawal(self, update):
        return
    
    def find_path_to_destination(self, destination):
        return
    
    def measure_reachability(self):
        return
    
    def collapse_routing_table(self):
        return


class RoutingTable(RoutingTable):
    def apply_announcement(self, update):
        '''
        Handle incoming route announcements
        announcement (dict): This contains entries for timestamp, source_as, next_hop, as_path, and destination_block.
        '''
        try:
            if self.time_of_earliest_update==sys.maxint: self.time_of_earliest_update=update['timestamp']
            self.time_of_latest_update=update['timestamp']
            #Conidtion when routing table don't have destination IP
            self.total_updates_received=self.total_updates_received+1
            if self.routing_table.get(update['destination_block'])==None:

                #add new destination_block into routing table and update TOTAL_UPDATES_RECEIVED

                self.routing_table[update['destination_block']]={'source_as':update['source_as'], 'timestamp':update['timestamp'], 'as_path':update['as_path'], 'next_hop':update['next_hop']}

            #Condition when routing table have this destination IP
            elif self.routing_table.get(update['destination_block'])!=None:
                #First check if "update"s as_path is or not shorter than routing_table's as_path
                temp={'source_as':update['source_as'], 'timestamp':update['timestamp'], 'as_path':update['as_path'], 'next_hop':update['next_hop']}
                if len(self.routing_table[update['destination_block']]['as_path'].split(' '))>len(update['as_path'].split(' ')):
                    self.routing_table.update({update['destination_block']:{'source_as':update['source_as'], 'timestamp':update['timestamp'], 'as_path':update['as_path'], 'next_hop':update['next_hop']}})
                    self.total_paths_changed=self.total_paths_changed+1
        except Exception as e:
            print(e)
            return False
        return True

class RoutingTable(RoutingTable):
    def apply_withdrawal(self, update):
        '''
        Handle incoming route withdrawals
        withdrawal (dict): This contains entries for timestamp, source_as, and destination_block.
        '''
        try:
            #if self.routing_table.get(update['destination_block'])==None:
                #return

            if self.routing_table.get(update['destination_block'])!=None:
                if self.routing_table[update['destination_block']]['source_as']==update['source_as']:
                    del self.routing_table[update['destination_block']]
                    self.total_paths_changed=self.total_paths_changed+1

            if self.time_of_earliest_update==sys.maxint: self.time_of_earliest_update=update['timestamp']
            self.time_of_latest_update=update['timestamp']
        except Exception as e:
            print(e)
            return False
        return True

class RoutingTable(RoutingTable):
    def measure_reachability(self):
        '''
        Measure reachability

        '''
        try:
            total = float(2**32)
            count = 0
            to_be_collapsed = []
            for k, _ in self.routing_table.iteritems():
                to_be_collapsed.append(ipaddr.IPv4Network(k))
            after_collapsed = ipaddr.collapse_address_list(to_be_collapsed)
            for each_network in after_collapsed:
                count += each_network.numhosts
            return count/total
        except Exception as e:
            print(e)
            return None

class RoutingTable(RoutingTable):
    def find_path_to_destination(self, destination):
        '''
        Find routes
        destination_ip_address (str): The destination IP address to which the packet must be routed.
        '''
        path = []
        dest = ipaddr.IPv4Network(destination)
        for cidr, v in self.routing_table.iteritems():
            entry = dict.fromkeys(['as_path', 'next_hop', 'prefix_len', 'source_as'], '') 
            curr_net = ipaddr.IPv4Network(cidr) # build network from CIDR address
            if dest in curr_net: # this method is a built in method to see whether one range of CIDR covers another
                entry['as_path'] = v['as_path']
                entry['next_hop'] = v['next_hop']
                entry['prefix_len'] = int(cidr.split('/')[1])
                entry['source_as'] = v['source_as']
                path.append(entry)
        path.sort(key = lambda x: x['prefix_len'], reverse=True)
        if len(path) == 0:
            return [{"as_path": None, "next_hop": None, "prefix_len": None, "source_as": None}]
        return path

# Routing table examples: (not part of the code comments, for my refrence only)
# ('207.150.245.0/24', {'timestamp': 1203380111, 'next_hop': '66.185.128.1', 
#                       'as_path': '1668 1239 18895 18895 18895 18895 18895', 'source_as': 1668})
# ('81.28.33.0/24', {'timestamp': 1203380112, 'next_hop': '195.22.216.188', 
#                    'as_path': '6762 3356 7473 12880 21341 21341 21341 21341 25306', 'source_as': 6762})
class RoutingTable(RoutingTable):
    def collapse_routing_table(self):
        '''
        Collapse routing table

        '''
        try:
            start = time.time()
            unique_route = set() # used to get screen unite 'san' combination, def of san see below
            time_stamps = {} # used to update timestamp
            to_be_collapsed = {} # used to store the to_be_collapsed list of CIDR network objects
            
            for k, v in self.routing_table.iteritems(): # k is CIDR, v is the other attributes (Dict)
                san = (v['source_as'], v['as_path'], v['next_hop']) # san: (source_as, as_path, next_hop) tuple
                if san not in unique_route:
                    unique_route.add(san)
                    to_be_collapsed[san] = [ipaddr.IPv4Network(k)] # collapse function need the network object as args
                    time_stamps[san] = v['timestamp']
                else: # san is in the set
                    to_be_collapsed[san].append(ipaddr.IPv4Network(k)) # add this CIDR to the to do list
                    if v['timestamp'] > time_stamps[san]: # update timestamp if current is larger
                        time_stamps[san] = v['timestamp']
                        
            new_routing_table = {} 
            for san, cidr in to_be_collapsed.iteritems(): # collapse CIDR
                after_collapsed_cidr = ipaddr.collapse_address_list(cidr) # collapsed CIDR list (may have more than one CIDR inside) 
                for each in after_collapsed_cidr: # for each CIDR, rebuild the routing table
                    cidr_str = str(each.ip)+'/'+str(each.prefixlen) # convert CIDR to string
                    # get timestamp, and unpack 'san'
                    new_routing_table[cidr_str] = {'timestamp': time_stamps[san], 'source_as': san[0], 
                                                   'as_path': san[1], 'next_hop': san[2]}
                    
            self.routing_table = new_routing_table
            end = time.time()
            print("*******************Time used: ****************************")
            print(end-start)
            print("*******************Time used****************************")
            return True
        except Exception as e:
            print(e)
            return False

