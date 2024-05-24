import json
import os
import time
import re
import requestUtil
from datetime import datetime
from web3 import Web3
from web3.middleware import geth_poa_middleware


eth_web3 = Web3(Web3.HTTPProvider("https://rpc.ankr.com/eth"))
bsc_web3 = Web3(Web3.HTTPProvider("https://rpc.ankr.com/bsc"))
bsc_web3.middleware_onion.inject(geth_poa_middleware, layer=0)
polygon_web3 = Web3(Web3.HTTPProvider("https://rpc.ankr.com/polygon"))
polygon_web3.middleware_onion.inject(geth_poa_middleware, layer=0)

ethscan_code_url = "https://etherscan.io/address/{address}#code"
bscscan_code_url = "https://bscscan.com/address/{address}#code"

ethscan_inputdata_url = "https://etherscan.io/tx/{tx}"
bscscan_inputdata_url = "https://bscscan.com/tx/{tx}"

ethscan_tx_url = "https://etherscan.io/txs?a={address}&p={page}"
bscscan_tx_url = "https://bscscan.com/txs?a={address}&p={page}"

## Etherscan cookies
cookies = """
cf_clearance=3SDbJFHr4coXbHpdq29bMDmbBbrt8Ka0AnsLGADRgt4-1699948943-0-1-9516ba5d.dc5cd74f.c217e5bd-250.0.0; _ga_T1JC9RNQXV=GS1.1.1699948943.19.1.1699948957.46.0.0; _ga=GA1.1.1014735669.1685338016; __stripe_mid=ba4e58e1-f707-437c-82f4-ad0c7952888464e1a0; etherscan_cookieconsent=True; ASP.NET_SessionId=ujgozaeysty4a3bhexnxmaiy; etherscan_offset_datetime=+8; _gid=GA1.2.1073836674.1699781542; __cflb=02DiuFnsSsHWYH8WqVXcJWaecAw5gpnmeviEreG1RcNHz
""".strip()

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0",
    "Cookie": cookies
}

## Bscscan cookies
# ……………………

tx_dict = {}

class EVMscan:

    def __int__(self, chain):
        self.chain = chain

    # calculate the delta time according to two block numbers
    def calculate_block_deltatime(self, block_number1, block_number2):
        if self.chain == "ETH":
            web = eth_web3
        elif self.chain == "BSC":
            web = bsc_web3
        elif self.chain == "Polygon":
            web = polygon_web3
        else:
            web = eth_web3
        block_info = web.eth.get_block(block_number1)
        datetime1 = datetime.utcfromtimestamp(block_info.timestamp)
        block_info2 = web.eth.get_block(block_number2)
        datetime2 = datetime.utcfromtimestamp(block_info2.timestamp)
        deltatime = datetime2 - datetime1
        return deltatime

    # crawl contract bytecode from Evmscan
    def crawl_bytecode(self, address):
        if self.chain == "ETH":
            code_url = ethscan_code_url
        elif self.chain == "BSC":
            code_url = bscscan_code_url
        else:
            code_url = ethscan_code_url
        resp = requestUtil.get(code_url.format(address = address), timeout=100, header=headers)
        try:
            code = (re.findall('<pre class="wordwrap scrollbar-custom.*?>(.*?)</pre>', resp.text)[0])
            print(code)
            return code
        except:
            title = requestUtil.get_title(resp)
            if "Ethereum BlockChain Explorer" in title:
                print(address + '  error')
            return ""

    # crawl tx inputdata from Evmscan
    def crawl_inputdata(self, tx):
        if self.chain == "ETH":
            inputdata_url = ethscan_inputdata_url
        elif self.chain == "BSC":
            inputdata_url = bscscan_inputdata_url
        else:
            inputdata_url = ethscan_inputdata_url
        resp = requestUtil.get(inputdata_url.format(tx = tx), timeout=100, header=headers)
        try:
            inputdata = (re.findall('<span id="rawinput" style="display:none".*?>(.*?)</span>',resp.text)[0])
            return inputdata
        except:
            title = requestUtil.get_title(resp)
            if "Ethereum BlockChain Explorer" in title:
                print(tx + '  error')
            return ""

    # crawl all transactions for one address
    def crawl_transaction(self, address, page = 1):
        global  tx_dict
        max_page = 10
        if self.chain == "ETH":
            tx_url = ethscan_tx_url
        elif self.chain == "BSC":
            tx_url = bscscan_tx_url
        else:
            tx_url = ethscan_tx_url
        resp = requestUtil.get(tx_url.format(address = address, page = page),proxable=True, header=headers, timeout=100)
        for t in re.findall('<a href="/tx/(.*?)".*?</a>.*?<td class><span style="max-width: 95px;" class="d-block badge bg-light border border-dark dark:border-white border-opacity-10 text-dark fw-normal text-truncate w-100 py-1.5" data-bs-toggle="tooltip" data-bs-boundary="viewport" data-bs-html="true" title="(.*?)">', resp.text, re.DOTALL):
            hash, sig = t
            if not sig in tx_dict:
                tx_dict[sig] = []
            tx_dict[sig].append(hash)
        if page == 1:
            last = re.findall('&amp;p=(.*?)"><span aria-hidden="True">Last', resp.text)
            if last:
                last_page = int(last[0].split('&amp;p=')[-1])
                for p in range(2, last_page+1 if last_page < 10 else max_page):
                    self.crawl_transaction(address, p)

    # judge whether funcstr is function str
    def judge_function(self, func_str):
        left_braket = []
        right_braker = []
        flag = True
        if '{' not in func_str:
            flag = False
            return flag, ''
        for i in func_str:
            if i =='{':
                left_braket.append(i)
                pos = func_str.index('{')
                break
            elif i == ';' or i == '}':
                flag = False
                return flag, ''
        for i in range(pos+1, len(func_str)):
            if len(left_braket) > len(right_braker):
                if func_str[i] == '{':
                    left_braket.append('{')
                elif func_str[i] == '}':
                    right_braker.append('}')
                pos = i
            else:
                pos = i
                break
        return flag, func_str[:pos]

    # given contract address and function_signature_str, crawl snippet code from EVMscan
    def crawl_snippet_code(self, address, signature):
        if self.chain == "ETH":
            code_url = ethscan_code_url
        elif self.chain == "BSC":
            code_url = bscscan_code_url
        else:
            code_url = ethscan_code_url
        resp = requestUtil.get(code_url.format(address = address), proxable=True, header= headers , timeout = 100)
        try:
            code = re.findall('</div><pre class="js-sourcecopyarea editor" id="editor.*? style="margin-top: 5px;">(.*?)</pre><br>', resp.text, re.DOTALL)[0]
        except:
            return False
        if not len(signature):
            return False
        if '(' in signature and ')' in signature:
            find_str, para_list = 'function ' + signature.split('(')[0] , signature.split('(')[1].strip(')').split(',')
            find_str = find_str + '\(.*?'
            for p in para_list:
                p = 'uint' if p== 'uint256' else p
                p = p.split('[')[0] + '\[]' if '[]' in p else p
                find_str = find_str + p +'.*?'
            find_str = find_str + '\)'
        elif signature == 'fallback':
            find_str = 'function()'
        func = re.findall(find_str + '.*?(?=function |$)', code, re.DOTALL)
        new_func = []
        for f in func:
            flag, new_f = self.judge_function(f)
            if flag:
                new_func.append(new_f)
        if len(new_func) >= 1:
            return new_func
        return False


class UsefulFunction:
    ## replace contract address to str 'address*'
    def replace_address(self, sequence):
        address = re.findall('0x[0-9a-zA-Z]{40}', sequence)
        num = 1
        address_dict = {}
        for a in address:
            if a not in address_dict:
                address_dict[a] = 'address' + str(num)
                num += 1
                project = sequence.replace(a, address_dict[a])
            else:
                continue
