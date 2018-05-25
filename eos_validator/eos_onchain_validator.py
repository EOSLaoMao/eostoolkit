#!/usr/bin/python
# -*- coding: utf-8 -*-
#
from __future__ import unicode_literals
import os
import sys
import time
import json
import argparse
import requests
import multiprocessing


def check_balance_signal_account(param):
    node_host, account_name, pub_key, snapshot_balance = param
    return snapshot_balance

def check_balance(node_host, snapshot_csv):
    EOS_TOTAL = 1000000000.0000
    account_onchain_balance_total = 0.0
    cpu_count = multiprocessing.cpu_count()
    process_pool = multiprocessing.Pool(processes=cpu_count)
    check_failed_flag = False

    try:
        with open(snapshot_csv, 'r') as fp:
            batch_lines = []
            for line in fp.readlines():
                _, account_name, pub_key, snapshot_balance = line.replace('"','').split(',')
                batch_lines.append((node_host, account_name, pub_key, float(snapshot_balance)))
                if len(batch_lines)<cpu_count*100:
                    continue
                results = process_pool.map(check_balance_signal_account, batch_lines, cpu_count)
                for signal_onchain_amount in results:
                    if signal_onchain_amount < 0:
                        return False
                    account_onchain_balance_total += signal_onchain_amount
                batch_lines = []
            if batch_lines:
                results = process_pool.map(check_balance_signal_account, batch_lines, cpu_count)
                for signal_onchain_amount in results:
                    if signal_onchain_amount < 0:
                        return False
                    account_onchain_balance_total += signal_onchain_amount

        print 'account_onchain_balance_total:', account_onchain_balance_total
    except Exception as e:
        print 'EXCEPTION: there are exception:', e
        return False
    finally:
        process_pool.close()
        process_pool.join()
        
    return True


def fetch_eos_balance(params):
    eth_addr, snapshot_balance, api_url, count = params
    url = api_url.format(eth_addr=eth_addr)
    res = requests.get(url)
    max_retry = 2
    while res.ok and max_retry > 0:
        print('retry request with params:', params)
        res = requests.get(url)
        max_retry -= 1
    if not res.ok:
        return False
    onchain_balance = res.json()
    if abs(float(onchain_balance['balance']) - snapshot_balance) < 0.0001:
        print count, "valid", snapshot_balance, onchain_balance['balance']
        return True
    print count, "INVALID", snapshot_balance, onchain_balance['balance']
    return False

def check_snapshot(snapshot_csv, api_url):
    cpu_count = multiprocessing.cpu_count()
    process_pool = multiprocessing.Pool(processes=cpu_count)
    count = 1
    fp = open(snapshot_csv)
    batch_lines = []
    try:
        for line in fp.readlines():
            account = eval('[%s]' % line)
            # print account
            eth_addr = account[0]
            snapshot_balance = float(account[3])
            batch_lines.append((eth_addr, snapshot_balance, api_url, count))
            count += 1
            if len(batch_lines) < 2*cpu_count:
                continue
            # print eth_addr, snapshot_balance
            print('a', len(batch_lines))
            results = process_pool.map(fetch_eos_balance, batch_lines, cpu_count)
            print('a results:', results)
            if len([r for r in results if not r]) > 0:
                print('INVALID')
                return
            batch_lines = []
        if batch_lines:
            print('b', len(batch_lines))
            results = process_pool.map(fetch_eos_balance, batch_lines, cpu_count)
            print('b results:', results)
            if len([r for r in results if not r]) > 0:
                print('INVALID')
                return
    except Exception as e:
        print 'EXCEPTION: there are exception:', e
        return False
    finally:
        process_pool.close()
        process_pool.join()


def main():
    parser = argparse.ArgumentParser(description='EOSIO onchain validator tool.')
    parser.add_argument('--action', type=str, required=True, help='snapshot_validate|chain_validate')
    parser.add_argument('--config', type=str, required=True, help='validator.json config file path')
    args = parser.parse_args()
    action, conf_file = args.action, os.path.abspath(os.path.expanduser(args.config))
    if action not in ('snapshot_validate', 'chain_validate'):
        print 'ERROR: action should be one of snapshot_validate|chain_validate'
        sys.exit(1)
    if not os.path.isfile(conf_file):
        print 'ERROR: validator config file not exist:',conf_file
        sys.exit(1)
    conf_dict = None
    with open(conf_file, 'r') as fp:
        aa = fp.read()
        print aa
        conf_dict = json.loads(aa)
    if not conf_dict:
        print 'ERROR: validator config can not be empty:',conf_file
        sys.exit(1)

    if action == 'snapshot_validate':
        if not check_snapshot(conf_dict['snapshot_csv'], conf_dict['api_url']):
            print 'ERROR: !!! The Snapshot Check FAILED !!!'
            sys.exit(1)
        else:
            print 'SUCCESS: !!! The Snapshot Check SUCCESS !!!'
            sys.exit(1)

    if action == 'chain_validate':
        if not check_balance(conf_dict['nodeosd_host'], conf_dict['snapshot_csv']):
            print 'ERROR: !!! The Balance Onchain Check FAILED !!!'
            sys.exit(1)
        else:
            print 'SUCCESS: !!! The Balance Onchain Check SUCCESS !!!'
            sys.exit(1)


if __name__ == '__main__':
    main()
