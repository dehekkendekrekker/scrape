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
import sys, os
from tqdm import tqdm
from lxml import html

OUTPUTTING = False

def error(message):
    sys.stderr.write("[!] %s\n" % message)

class Link:
        filename = None
        url      = None
        title    = None

        def __init__(self, filename, title, url):
            self.filename = urllib.unquote(filename)
            self.url = url
            self.title = title.encode("ascii", "ignore")

def update_hook(t):
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
    '''
    Requests usr input on which files to download.
    Accepts: \d,\d-\d
    :return: list of indices
    '''
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


def assemble_link_list(root):
    '''
    Put a tag info in more usable Link objects
    :return: dict index => Link
    '''
    tree = html.fromstring(result)
    elements = tree.xpath("//a")

    links = dict()
    i = 0
    # Process each a-tag in the element list
    for element in elements:
        if element.xpath("./@href") and element.xpath("./text()"):
            filename = element.xpath("./@href")[0]
            if not "/" in filename and not "\0" in filename:
                links[i] = Link(element.xpath("./@href")[0], element.xpath("./text()")[0],
                                    "%s%s" % (root, element.xpath("./@href")[0]))
                i += 1

    return links

def get_max_file_name_len(download_list):
    '''
    Determines the longest filename to be used in properly formatting output

    :param download_list: integer index dict specifying links
    :return: int
    '''
    name_length = 0
    for key in download_list:
        if len(links[key].filename) > name_length:
            name_length = len(links[key].filename)

    return name_length

if __name__ == "__main__":
    TITLE_COL_WIDTH = 100
    THREAD_COUNT    = 5
    POSITION        = -1

    parser = argparse.ArgumentParser(description='Scrape links from URL, select and download')
    parser.add_argument('url', type=str, nargs=1, help='url of site to scrape')
    parser.add_argument('dest', type=str, nargs=1, help='desination directory of the downloaded files')

    args = parser.parse_args()

    url = args.url[0]
    dest = args.dest[0].rstrip("/")

    # Url reparation
    if not url[-1:] == "/":
        url = url + "/"

    result = requests.get(url).content
    links  = assemble_link_list(url)
    name_length = get_max_file_name_len(links)

    if len(links) == 0:
        error("This URL contains no files that can be downloaded with this script")
        exit(-1)

    # Display the files
    for index in links:
        formatted_index = str(index) + ")"
        formatted_index = formatted_index.ljust(3, " ")
        print "%s %s" % (formatted_index, links[index].filename.ljust(name_length, " "))

    print ""
    print "Enter comma separated sequence of ids or ranges that need to be downloaded. eg 1,4,7-18"
    print "Enter q to quit"

    input = handle_user_input()
    download_list = input & links.viewkeys()
    name_length = get_max_file_name_len(download_list)

    for item in [x for x in download_list]:
        filename = dest + "/" + links[item].filename
        if os.path.isfile(filename):
            error("%s already exists" % filename)
            download_list.remove(item)

    if not len(download_list):
        error("Nothing to do ..")
        exit(-1)

    try:
        print "Download %i files" % len(download_list)

        for item in download_list:
            link = links[item]
            label = "%s" % link.filename.ljust(name_length, " ")
            filename = dest + "/" + link.filename

            with tqdm(unit='B', ncols=0, unit_scale=True, mininterval=2, desc=label) as t:
                urllib.urlretrieve(link.url, filename=filename, reporthook=update_hook(t), data=None)
    except KeyboardInterrupt:
        error("Aborted")
        exit(-1)
