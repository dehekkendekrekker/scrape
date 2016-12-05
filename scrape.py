#!/bin/python2

__author__ = 'parallax'

'''
Requirements:

Python 2.7

argparse    | pip2 install argparse
requests    | pip2 install requests
urllib      | pip2 install urllib
tqdm        | pip2 install tqdm
lxml        | pip2 install lxml


'''


import argparse
import requests
import urllib
import sys, signal, time
from tqdm import tqdm
from lxml import html
import threading
from Queue import Queue

def error(message):
    sys.stderr.write("[!] %s" % message)

class Link:
        filename = None
        url      = None
        title    = None

        def __init__(self, filename, title, url):
            self.filename = urllib.unquote(filename)
            self.url = url
            self.title = title


class DownloadThread(threading.Thread):
    def __init__(self, queue, destfolder, position, name_length):
        super(DownloadThread, self).__init__()
        self.queue = queue
        self.destfolder = destfolder
        self.daemon = True
        self.position = position
        self.name_length = name_length

    def run(self):
        while True:
            link = self.queue.get()
            try:
                self.download_link(link)
            except Exception,e:
                print "   Error: %s"%e
            self.queue.task_done()

    def download_link(self, link):
        label = link.filename.ljust(self.name_length)
        filename = self.destfolder + "/" + link.filename

        with tqdm(unit='B', unit_scale=True, miniters=1, position=self.position, desc=label, dynamic_ncols=True) as t:  # all optional kwargs
            urllib.urlretrieve(link.url, filename=filename, reporthook=self.update_hook(t), data=None)

    def update_hook(self, t):

      last_b = [0]

      def inner(b=1, bsize=1, tsize=None):
        """
        b  : int, optional
            Number of blocks just transferred [default: 1].
        bsize  : int, optional
            Size of each block (in tqdm units) [default: 1].
        tsize  : int, optional
            Total size (in tqdm units). If [default: None] remains unchanged.
        """
        if tsize is not None:
            t.total = tsize
        t.update((b - last_b[0]) * bsize)
        last_b[0] = b
      return inner


def handle_user_input():
    sanitized_input = []
    response = raw_input("> ")
    if response == "q":
        exit(-1)
    input = response.split(",")
    for element in input:
        if not element:
            continue

        # Check for a range. ie. 5-7
        if "-" in element:
            left, right = element.split("-", 1)

            if not left.isdigit() or not right.isdigit():
                error("Invalid input")
                exit(-1)

            sanitized_input.extend(range(int(left), int(right) + 1))

        else:
            if not element.isdigit():
                error("Invalid input")
                exit(-1)

            sanitized_input.append(int(element.strip()))

    return sanitized_input


def assemble_link_list():
    tree = html.fromstring(result)
    elements = tree.xpath("//a")
    links = dict()
    start = 0
    # Process each a-tag in the element list
    for element in elements:
        links[start] = Link(element.xpath("./@href")[0], element.xpath("./text()")[0],
                            "%s%s" % (url, element.xpath("./@href")[0]))
        start += 1

    return links

def get_max_file_name_len(download_list):
    name_length = 0
    for key in download_list:
        if links[key].filename >= name_length:
            name_length = len(links[key].filename)

    return name_length

if __name__ == "__main__":
    TITLE_COL_WIDTH = 100

    parser = argparse.ArgumentParser(description='Scrape links from URL, select and download')
    parser.add_argument('url', type=str, nargs=1, help='url of site to scrape')
    parser.add_argument('dest', type=str, nargs=1, help='desination directory of the downloaded files')

    args = parser.parse_args()

    url = args.url[0]
    dest = args.dest[0]

    # Url reparation
    if not url[-1:] == "/":
        url = url + "/"

    result = requests.get(url).content
    links  = assemble_link_list()

    # Display the files
    for index in links:
        print "%s) %s" % (index, links[index].title.ljust(TITLE_COL_WIDTH))

    print ""
    print "Enter comma separated sequence of ids or ranges that need to be downloaded. eg 1,4,7-18"
    print "Enter q to quit"

    input = handle_user_input()
    download_list = input & links.viewkeys()
    name_length = get_max_file_name_len(download_list)

    queue = Queue()
    for item in download_list:
        queue.put(links[item])

    position = 0

    for i in range(5):
        t = DownloadThread(queue, dest, position, name_length)
        t.start()
        position +=1

    try:
        while True:
            if not queue.empty():
                time.sleep(1)
                continue
    except KeyboardInterrupt:
        error("Aborted")
        exit(-1)
