
import sys
import re
import shutil
import os
import json
import os.path as path
from urlparse import urlparse

from browsermobproxy import Server
from selenium import webdriver


def visit_urls_from_file(filename=None):
    """
    Visits urls from an input file and generates HAR files for each URL
    visited.

    :filename=None: Path to a file containing urls separated by newlines.
    :returns:       None.
    """
    # Check that the file exists.
    if not path.exists(filename):
        raise FileNotFoundError("Specified file {} not found.".format(filename))

    # Read in the specified file. If no errors occur, create a new web driver,
    # open the specified URLs, record the requests, and kill the connection.
    with open(filename, "r") as f:
        files = f.readlines()

    # Clean out the folder to re-make all the data.
    clean("./har-data/")
    os.mkdir("./har-data/")

    # Create browsermob proxy server.
    server = Server("./browsermob-proxy-2.1.4/bin/browsermob-proxy")
    server.start()
    proxy = server.create_proxy()

    # Proper selenium setup.
    profile = webdriver.FirefoxProfile()
    profile.set_proxy(proxy.selenium_proxy())
    driver = webdriver.Firefox(firefox_profile=profile)

    # Used to account for any potential blank lines in file (thanks James!)
    files = [x for x in files if(len(x)>1)]

    # Iterate over all the URLs, making HARs along the way.
    for url in files:
        # If the url doesn't have *at least* an http prefix, Selenium gets mad.
        if "http" not in url:
            url = "http://" + url
        
        # Do url stuff.
        url, hostname, hostpath, subs = format_url(url)
        proxy.new_har(
            url, 
            options={
                "captureHeaders": True,
                "captureContent": True,
                "captureBinaryContent": True
            }
        )  
        driver.get(url)

        # If the path doesn't already exist, make it. However, if we need to
        # make subdirectories, make them, too.
        if not path.exists(hostpath):
            os.mkdir(hostpath)

        # Check whether the list of subdirectories is empty. If not, start
        # making subdirectories.
        if subs:
            # For each directory in the list of subdirectories, create a new
            # deepest path, i.e., a path that is deeper than the host path. If
            # that directory already exists, *don't* try to make a new
            # directory of the same name. Keep adding on portions of the
            # url path until we find a deepest path that doesn't exist, then
            # create it.
            for directory in subs:
                deepest_path = path.join(hostpath, directory)
                if not path.exists(deepest_path):
                    os.mkdir(deepest_path)
                hostpath = deepest_path

        # Dump the har to a file, as before.
        with open(path.join(hostpath, "{}.har".format(hostname + "." + ".".join(subs))), "w") as f:
            f.write(json.dumps(proxy.har))

    # Close the connection so we don't get `FileNotFoundError`s.
    server.stop()
    driver.quit()


def clean(filepath):
    """
    Recursively cleans the specified directory.

    :path="":   Directory to clean.
    :returns:    None.
    """
    if path.exists(filepath):
        shutil.rmtree(filepath)


def format_url(url):
    """
    Returns a tuple of (url, hostname, hostpath, subdirectories).

    :url:       A url.
    :returns:   A tuple containing the url, hostname, hostpath, and path of
                the subdirectory tree to be made.
    """
    # Strip the url of any extraneous characters (line endings, etc.)
    url = url.strip()

    # Split the url by pattern-matching on the http(s) prefix we added before.
    urlsplit = re.split(r"(https?://)", url)

    # Generate a hostname from the split url, but as we can't encode a slash
    # into a filename, replace it with a dot.
    hostname = (urlsplit[1] + urlsplit[2]).replace("://", ".").split("/")[0]

    # Create a root path for this host.
    hostpath = "./har-data/{}/".format(hostname)

    # Create a list of subdirectories necessary to store har files for this url.
    subs = urlparse(url)[2].split("/")[1:]

    return url, hostname, hostpath, subs


if __name__ == "__main__":
    # Make sure that the gecko drivers are in PATH.
    os.environ["PATH"] = "./:" + os.environ["PATH"]

    # Call the main function.
    visit_urls_from_file(sys.argv[1])
