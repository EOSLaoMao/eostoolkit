import requests

CONTRACT = "0x86fa049857e0209aa7d9e616f7eb3b3b78ecfdb0"
API = "https://api.tokenbalance.com/token/{contract}/{eth_addr}"

def fetch_eos_balance(eth_addr):
    url = API.format(contract=CONTRACT, eth_addr=eth_addr)
    res = requests.get(url)
    result = res.json()
    return result

def validate(snapshot_csv):
    count = 1
    fp = open(snapshot_csv)
    for line in fp.readlines():
        account = eval('[%s]' % line)
        # print account
        eth_addr = account[0]
        snapshot_balance = float(account[3])
        # print eth_addr, snapshot_balance
        onchain_balance = fetch_eos_balance(eth_addr)
        print count, "validating", snapshot_balance, onchain_balance['balance']
        '''
        if abs(float(onchain_balance['balance']) - snapshot_balance) < 0.0001:
            print count, "valid", snapshot_balance, onchain_balance['balance']
        else:
            print count, "INVALID", snapshot_balance, onchain_balance['balance']
            break
        '''
        count += 1


if __name__ == '__main__':
    validate('./snapshot.csv')
