"""Generate network dependency tree.

Author:
    Jacinta Hu

About:
    This script generates the network dependency tree of a site by reading its network logs.

Todo:
    How to deal with duplicates? Sometimes they appear at different branches in the tree,
    and the only way I can think of to deal with them is to really dig into the initiator call
    stack and that sounds absolutely disgusting

"""

import time
import bisect
import json
import logging
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.common.exceptions import InvalidArgumentException
from anytree import AnyNode, RenderTree
import anytree.cachedsearch


def wait_for_load(driver):
    """Wait for page source to stop changing."""
    html = driver.page_source
    time.sleep(0.5)
    while html != driver.page_source:
        html = driver.page_source
        time.sleep(0.5)


def parse_log(driver, timestamp):
    """Build tree of network requests since timestamp."""
    log = driver.get_log('performance')
    log = log[bisect.bisect_left(
        [entry['timestamp'] for entry in log], timestamp):]
    log = [json.loads(entry['message'])['message'] for entry in log]

    requests = []
    data_received = []
    for message in log:
        if message['method'] == 'Network.requestWillBeSent':
            request_id = message['params']['requestId']
            request_url = message['params']['request']['url']
            initiator = message['params']['initiator']
            type_ = message['params']['type']
            if initiator['type'] == 'script':
                initiator = initiator['stack']
                while 'parent' in initiator:
                    initiator = initiator['parent']
                initiator = initiator['callFrames'][-1]['url']
            elif initiator['type'] == 'parser':
                initiator = initiator['url']
            else:
                initiator = initiator['type']
            requests.append({'id': request_id, 'url': request_url,
                             'initiator': initiator, 'type': type_})
        elif message['method'] == 'Network.dataReceived':
            data_received.append(message['params']['requestId'])
    return [r for r in requests if r['id'] in data_received]

def main():
    """Main function."""
    logging.basicConfig(level=logging.DEBUG)
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--auto-open-devtools-for-tabs')
    caps = DesiredCapabilities.CHROME
    caps['goog:loggingPrefs'] = {'performance': 'ALL'}
    chrome_options.add_experimental_option(
        'perfLoggingPrefs', {'enablePage': True})
    driver = webdriver.Chrome(options=chrome_options,
                              desired_capabilities=caps)
    while True:
        website = input("Enter the site to analyze: ")
        epoch_in_milliseconds = time.time() * 1000
        try:
            driver.get(website)
        except InvalidArgumentException as err:
            logging.error(str(err))
            continue
        wait_for_load(driver)
        resources = parse_log(driver, epoch_in_milliseconds)
        tree = AnyNode(id='root', url='', type='Default', count=1)
        AnyNode(parent=tree, id='other', url='other', type='Default', count=1)
        AnyNode(parent=tree, id='preload',
                url='preload', type='Default', count=1)
        for res in resources:
            parent = anytree.cachedsearch.findall(
                tree, lambda node, req=res: node.url == req['initiator'])
            if not parent:
                logging.info(
                    "Could not find initiator %s, creating now", res['initiator'])
                parent = AnyNode(
                    parent=tree, id=res['initiator'], url=res['initiator'], type='Unknown', count=1)
            else:
                # Attach node to first instance of parent if multiple matches
                parent = parent[0]
            match = anytree.cachedsearch.findall(
                tree, lambda node, req=res: node.url == req['url'])
            if not match:
                AnyNode(id=res['id'], parent=parent,
                        url=res['url'], type=res['type'], count=1)
            else:
                for node in match:
                    if node and node.parent == parent:
                        logging.warning('Duplicate script! %s', res['url'])
                        node.count += 1
        for pre, _, node in RenderTree(tree):
            print(pre, node.type, node.count, end=' ')
            if node.url[:4] == 'data':
                print('data')
            else:
                print(node.url[:100])
    driver.close()

if __name__ == "__main__":
    main()
