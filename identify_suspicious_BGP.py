import glob
from pybgpdump import BGPDump
from dpkt import bgp
import ipaddr
import socket
import time
import sys
from collections import defaultdict
import struct
from datetime import datetime

def monitor_updates_to_range(rt, filelist, monitored_range):
    '''
    Monitoring route updates to specific prefixes
    rt (RoutingTable): The RoutingTable instance which will be updated.
    filelist (list): Contains the MRT filenames from which updates should be added to rt.
    monitored_range (ipaddr.IPv4Network): The CIDR range that we will monitor updates for.
    '''
    targeted_updates = {'announcements':[], 'withdrawals':[]}
    
    
    for each_file in filelist:
        pu = ParseUpdates(filename = each_file)
        pu.parse_updates()
        updates = pu.get_next_updates()
        while True:
            next_updates = updates.next()
            try:
                n_announcements =  len(next_updates["announcements"])
            except TypeError:
                n_announcements = 0
            try:
                n_withdrawals =  len(next_updates["withdrawals"])
            except TypeError:
                n_withdrawals = 0
            if next_updates["timestamp"] == None:
                break
                
            for i in range(0, n_announcements):
                updated_net = ipaddr.IPv4Network(next_updates["announcements"][i]['destination_block'])
                if updated_net.overlaps(monitored_range):
                    targeted_updates['announcements'].append(next_updates["announcements"][i])
                    rt.apply_announcement(next_updates["announcements"][i])
                
            for i in range(0, n_withdrawals):
                updated_net = ipaddr.IPv4Network(next_updates["withdrawals"][i]['destination_block'])
                if updated_net.overlaps(monitored_range):
                    targeted_updates['withdrawals'].append(next_updates["withdrawals"][i])
                    rt.apply_withdrawal(next_updates["withdrawals"][i])
    # Print the announcements which resulted in routing table changes.   
    print('The announcements which resulted in routing table changes in targeted range:')
    for each_update in targeted_updates['announcements']:
        print(each_update)
    # Print the withdrawals which resulted in routing table changes.   
    print('The withdrawals which resulted in routing table changes in targeted range:')
    for each_update in targeted_updates['withdrawals']:  
        print(each_update)   
    return rt, targeted_updates

def is_update_suspicious(rt, filelist, monitored_range):
    '''
    Identify suspicious updates
    Arguments:

    rt (RoutingTable): The RoutingTable instance which will be updated.
    filelist (list): Contains the MRT filenames from which updates should be added to rt.
    monitored_range (ipaddr.IPv4Network): The CIDR range that we will monitor updates for.
    Returns:

    The updated rt object.
    A list of updates that were marked as suspicious.
    A list of updates that came from an AS which made atleast one suspicious update.
    A list of updates that came from an AS that was the victim of the suspicious update (i.e., the destination AS of the route would have been replaced by the suspicious announcement).
    
    announcement is suspicious if it satisfies both the following conditions:
    the AS path appears to terminate at an AS which has never advertised a route to addresses in this range before
    it is for a more specific range than any existing entries in the the routing table

    '''
    targeted_updates = {'announcements':[]}
    safe_advertising_as = []
    suspicious_updates = []
    suspicious_as = set()
    updates_from_suspicious_as = []
    victim_as = set()
    victim_updates = []
    routing_dest_blocks = set() # store (ip, mask) tuple from safe updates to help below algm
    
    
    for each_file in filelist:
        pu = ParseUpdates(filename = each_file)
        pu.parse_updates()
        updates = pu.get_next_updates()
        while True:
            next_updates = updates.next()
            try:
                n_announcements =  len(next_updates["announcements"])
            except TypeError:
                n_announcements = 0
            if next_updates["timestamp"] == None:
                break
            for i in range(0, n_announcements):
                updated_net = ipaddr.IPv4Network(next_updates["announcements"][i]['destination_block'])
                if updated_net in monitored_range:
                    
                    cidr =  next_updates["announcements"][i]['destination_block']
                    ip, mask = cidr.split('/')[0], cidr.split('/')[1]
                    # current update ending AS:
                    curr_termination = next_updates["announcements"][i]['as_path'].split(' ')[-1]
                    # if new update source AS is from suspicious AS:
                    if next_updates["announcements"][i]['source_as'] in suspicious_as:
                        updates_from_suspicious_as.append(next_updates["announcements"][i])
                    if curr_termination in suspicious_as: 
                        suspicious_updates.append(next_updates["announcements"][i])
                        # add the victim AS: old suspicious, maybe new victim
                        old_routing = rt.routing_table.get(cidr) # find old routing entry
                        if old_routing: # if found
                            old_as = old_routing['as_path'].split(' ')[-1] # last AS is the victim
                            if old_as not in suspicious_as: victim_as.add(old_as)
                        break
                        
                    flag1, flag2, flag3 = False, True, False # read further to understand
                    # Test suspicious condition1:
                    if curr_termination not in safe_advertising_as:
                        flag1 = True
                        
                    # Test suspicious condition2:
                    for each_net in routing_dest_blocks:
                        # if there exists one dest more specific than (or equally with)
                        # the dest in this update, set flag2 to false, which means it's safe
                        if ipaddr.IPv4Network(cidr) not in ipaddr.IPv4Network('/'.join(each_net)):
                            flag2 = False
                            break
                            
                    # exception: if ip in this update is new, then don't list as suspicious 
                    for each_net in routing_dest_blocks:
                        if ip == each_net[0]: # if found, means it's old, then no more meet exception
                            flag3 = True
                            break
                            
                    # determine whether it's a suspicious or not
                    if flag1 and flag2 and flag3:
                        # new suspicious, add new victim AS:
                        old_routing = rt.routing_table.get(cidr) # find old routing entry
                        if old_routing: # if found
                            old_as = old_routing['as_path'].split(' ')[-1] # last AS is the victim
                            if old_as not in suspicious_as: victim_as.add(old_as)
                        suspicious_as.add(curr_termination)
                        suspicious_updates.append(next_updates["announcements"][i])
                        continue # jump to next update
                    # if old victim send an annoucement
                    if curr_termination in victim_as:
                        victim_updates.append(next_updates["announcements"][i])
                        
                    # Now we rule out it's suspicious, lets apply announcement and add the as in safe list
                    targeted_updates['announcements'].append(next_updates["announcements"][i])
                    safe_advertising_as.append(next_updates["announcements"][i]['source_as'])
                    rt.apply_announcement(next_updates["announcements"][i])
                    routing_dest_blocks.add((ip, mask))
    victim_as = victim_as.difference(suspicious_as) 
    print('-------------------Suspicious AS below:-------------------')
    for each_suspicious in suspicious_as:
        print(each_suspicious)
    print('-------------------Victim AS below:-------------------')
    for each_victim in victim_as:
        print(each_victim)
        
    # Print the announcements which resulted in routing table changes.   
#     for each_update in targeted_updates['announcements']:
#         print('The announcements which resulted in routing table changes in targeted range:')
#         print(each_update)
    suspicious_updates.sort(key = lambda x: x['timestamp'])
    updates_from_suspicious_as.sort(key = lambda x: x['timestamp'])
    victim_updates.sort(key = lambda x: x['timestamp']) 
    return rt, suspicious_updates, updates_from_suspicious_as, victim_updates

def as_org_mapper(mapping_path, keyed_by_as=True, as_list=['17557', '36561']):
    '''
    Mapping AS numbers to organizations
    Arguments:
    mapping_path (str): Path to the CAIDA AS to org mapping.
    keyed_by_as (bool): True (default) will cause this function to return a dictionary with AS numbers as keys. False will cause this function to return a dictionary with organization names as keys.
    Returns: A dictionary of AS to organization mappings.
    '''
    temp1, temp2 = {}, {}

    with open(mapping_path, 'r') as f:
        for line in f: # first iter to find the Org Code by As Num
            for each_as in as_list:
                if each_as == line.split('|')[0]:
                    temp1[each_as] = line.split('|')[3]

    with open(mapping_path, 'r') as f:
        for line in f: # second iter to find Org name by Org Code
            for k, v in temp1.items():
                if v == line.split('|')[0]:
                    temp2[k] = line.split('|')[2]

    for each in as_list:
        temp1[each] = temp2[each]
        
    match_num = temp1
    match_org = {}
    
    for k, v in match_num.items():
        match_org[v] = k

    return match_num if keyed_by_as else match_org

def tell_story(suspicious_updates, victim_updates, mapping):
    '''
    Telling the story of a BGP hijack with data
    '''
    story = []
    sus_name = mapping[suspicious_updates[0]['as_path'].split(" ")[-1]]
    vic_name = mapping[victim_updates[0]['as_path'].split(" ")[-1]]
    for each in suspicious_updates:
        time = datetime.utcfromtimestamp(int(each['timestamp'])).strftime('%Y-%m-%d %H:%M:%S')
        string = time+': route announcement for '+each['destination_block']+' from suspicious as '+sus_name+' : '+each['as_path']+' victim as was '+vic_name
        story.append([int(each['timestamp']), string])
    for each in victim_updates:
        time = datetime.utcfromtimestamp(int(each['timestamp'])).strftime('%Y-%m-%d %H:%M:%S')
        string = time+': route announcement for '+each['destination_block']+' from victim as '+vic_name+' : '+each['as_path']
        story.append([int(each['timestamp']), string])
    story.sort(key=lambda x: x[0])
    for each in story:
        print(each[1])
    return
