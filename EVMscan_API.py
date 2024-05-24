import os

import web3
import json
import requestUtil

eth_url = "https://api.etherscan.io/api?module=contract&action=getsourcecode&address={address}&apikey={key}"
bsc_url = "https://api.bscscan.com/api?module=contract&action=getsourcecode&address={address}&apikey={key}"
polygon_url = "https://api.polygonscan.com/api?module=contract&action=getsourcecode&address={address}&apikey={key}"

class EVMscan_API:
    def __int__(self, chain):
        self.chain = chain

    # get the contract source code from etherscan api
    def get_source_code(self, address, source_dir):
        if self.chain == "ETH":
            url = eth_url
        elif self.chain == "BSC":
            url = bsc_url
        elif self.chain == 'Polygon':
            url = polygon_url
        else:
            url = eth_url
        resp = requestUtil.get(url, timeout=100)

        try:
            if json.loads(resp.text)['result'][0]['ABI'] == 'Contract source code not verified':
                return 'Contract source code not verified'
            with open(f'{source_dir}/{address}.txt', 'w', encoding='utf-8') as f:
                f.write(json.loads(resp.text)["result"][0]['SourceCode'])
                f.close()
        except Exception as error:
            print(error)
            return 'error'

    ## func get_source_code can get the source code, however the position of dependent contract is disorder
    ## enbale the source code compile, it may encounter three situations.
    # source_dir: source_code from evmscan api, which probably can't be compiled
    # target_dir：source_code that have been processed
    def analyze_source_code(self, source_dir, target_dir):
        for file in os.listdir(source_dir):
            address = file.split('.')[0]
            path = os.path.join(source_dir, file)
            flag = 0
            with open(path, 'r', encoding='utf-8') as file:
                data = file.read()
                if not data.startswith('{'):
                    return
                elif data.startswith("{{"):
                    data = data[1:-1]
                    flag = 1
                read_data = json.loads(data)
                if type(read_data) == dict and flag:
                    contracts = read_data['sources']
                    for contract in contracts:
                        code = contracts[contract]['content']
                        if not os.path.exists(f'{target_dir}/{address}'):
                            os.makedirs(f'{target_dir}/{address}')
                        directory = f'{target_dir}/{address}/' + contract[:contract.rfind('/')]
                        if not os.path.exists(directory):
                            os.makedirs(directory)
                        contract_path = os.path.join(directory, contract.split('/')[-1])
                        with open(contract_path, 'w', encoding = 'utf-8') as contract_file:
                            contract_file.write(code)
                        print(contract,  '写入完毕')
                elif type(read_data) == dict:
                    for contract in read_data:
                        code = read_data[contract]['content']
                        if not os.path.exists(f'{target_dir}/{address}'):
                            os.makedirs(f'{target_dir}/{address}')
                        contract_path = os.path.join(f'{target_dir}/{address}', contract)
                        with open(contract_path, 'w', encoding = 'utf-8') as contract_file:
                            contract_file.write(code)
                        print(contract,  '写入完毕')


