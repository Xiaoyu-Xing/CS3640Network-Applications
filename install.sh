#!/bin/bash

# update ubuntu
yes | sudo apt-get update

# install geckodrivers for ff
wget https://github.com/mozilla/geckodriver/releases/download/v0.23.0/geckodriver-v0.23.0-linux64.tar.gz
tar xzvf ./geckodriver-v0.23.0-linux64.tar.gz
rm ./geckodriver-v0.23.0-linux64.tar.gz*

# install java (because it doesn't come preinstalled on ubuntu?!?)
yes | sudo apt-get install default-jre

# install browsermob-proxy
wget https://github.com/lightbody/browsermob-proxy/releases/download/browsermob-proxy-2.1.4/browsermob-proxy-2.1.4-bin.zip
unzip ./browsermob-proxy-2.1.4-bin.zip
rm browsermob-proxy-2.1.4-bin.zip*
