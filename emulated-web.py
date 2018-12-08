from mininet.log import setLogLevel
from mininet.util import dumpNodeConnections
from mininet.topolib import TreeNet
from shutil import copyfile
import re
import os
import sys
import time


def emulated_web(parsed_objects='./parsed-objects', url_list='./url_list'):
    '''
    parsed_objects: a directory storing objects under 'hostname' subfolder
    url_list: each line is a url to visit


    '''
    hosts = []
    objects_for_hosts_dict = {}
    source_files = {}
    # get hostnames and hostname:objects pairs in dict
    for i, (root, folders, files) in enumerate(os.walk(parsed_objects)):
        if i == 0:
            hosts = folders
        else:
            objects_for_hosts_dict[hosts[i-1]] = files
            source_files[root] = files
    # print(hosts, objects_for_hosts_dict)
    # list servable-content
    if not os.path.exists("./servable-content/"):
        os.mkdir("./servable-content/") # make dir
    for host, objects_list in objects_for_hosts_dict.iteritems():
        with open("./servable-content/"+host, "w+") as f:
            for i in objects_list:
                f.write(i+'\n') # each line contains one object

    # to simply the topo, use default method of tree structure with one level, n leaves
    server_num = len(hosts)
    host_server_match = {}
    for i in range(server_num):
        host_server_match['h'+str(i+2)] = hosts[i]
    # one client as 'h1', with server_num of servers fron 'h2' to 'hn'
    net = TreeNet(depth=1, fanout=server_num+1)
    # Add NAT connectivity
    net.addNAT().configDefault()
    net.start()

    # test this net
    dumpNodeConnections(net.hosts) # see connectivity
    print(net.pingAll()) # ping to test connectivity

    # set up simple http server
    for num, host in host_server_match.iteritems():
        print(str(os.path.join(parsed_objects, host)))
        net.get(num).cmd('cd %s' % str(os.path.join(parsed_objects, host)))
        net.get(num).cmd('python -m SimpleHTTPServer 80 &')
    # test each server http
    client = net.get('h1')
    time.sleep(2) # magic, don't delete, otherwise wget doesn't work
    for num, host in host_server_match.iteritems():
        # test for LAN
        # print(client.cmd('ping -c1 %s' % net.get(num).IP()))
        print(client.cmd('ping -c1 8.8.8.8'))
        # test for real
        print(client.cmd('wget -o - %s' % net.get(num).IP()))
        # print(client.cmd('wget -o - http://www.google.com'))
        time.sleep(1) # magic, don't delete, otherwise wget doesn't work

    if not os.path.exists("./get-responses/"):
        os.mkdir("./get-responses/") # make dir
        pass # not finished here


# for finalizaiton use:

if __name__ == "__main__":
    
    os.environ["PATH"] = "./:" + os.environ["PATH"]
    parsed_objects, url_list = sys.argv[1], sys.argv[2]
    emulated_web(parsed_objects=parsed_objects, url_list=url_list)