"""
Adding new users to WireGuard. Enter usernames dividing them by space.
Main config file must be named as 'wg0.conf'.
If you use another name specify it in variable 'conf_name', string 9 instead of 'wg0.conf
'"""

import os
from configparser import ConfigParser
import requests

conf_name = 'wg0.conf'


def get_last_user(conf_name):
    with open(conf_name, 'r') as conf:
        for line in conf:
            words = line.replace('\n', '').split()
            if len(words) >= 1:
                if words[0].lower() == 'allowedips':
                    ip = words[2]
    ip = ip.split('.')
    return ip[3].split('/')[0]


def get_port(conf_name):
    with open(conf_name, 'r') as conf:
        for line in conf:
            words = line.replace('\n', '').split()
            if len(words) >= 1:
                if words[0] == 'ListenPort':
                    port = words[2]
    return port


def generate_key(user):
    print('generating keys for ' + user)
    gen_key_command = f'wg genkey | tee {user}-private.key | wg pubkey > {user}-public.key'
    os.system(gen_key_command)
    with open(user + '-private.key') as pv_key_file:
        pv_key = pv_key_file.readline().replace('\n', '')
    with open(user + '-public.key') as pb_key_file:
        pb_key = pb_key_file.readline().replace('\n', '')
    print('done')
    print(pv_key, pb_key)
    return pv_key, pb_key


def new_user_config(user, pv_key, port, ip, server_pb_key, user_number):
    print('Creating new config for user ' + user)
    config = ConfigParser()
    config.add_section("Interface")
    config.set('Interface', "PrivateKey", str(pv_key))
    config.set('Interface', "Address", '10.0.0.' + str(user_number) + '/32')
    config.set('Interface', "DNS", '8.8.8.8, 1.1.1.1')
    config.add_section('Peer')
    config.set('Peer', "PublicKey", str(server_pb_key))
    config.set('Peer', "AllowedIPs", '0.0.0.0/0')
    config.set('Peer', "Endpoint", str(ip) + ':' + str(port))
    config.set('Peer', "PersistentKeepalive", '20')
    with open(user + '.conf', "w") as config_file:
        config.write(config_file)
    print('Done')


def add_to_main(pb_key, user_number, user, conf_name):
    print('Adding user ' + user + ' to wg0.conf')
    config = ConfigParser()
    config.add_section('Peer')
    config.set('Peer', "PublicKey", str(pb_key))
    config.set('Peer', "AllowedIPs", '10.0.0.' + str(user_number) + '/32')
    with open(conf_name, 'a') as main_conf:
        config.write(main_conf)
    print('Done')


def main():
    usernames = input("Enter the names of new clients separated by spaces").split()
    user_number = int(get_last_user(conf_name)) + 1
    server_ip = requests.get('https://api.ipify.org').text
    port = get_port(conf_name)

    try:
        with open('server_public.key', 'r') as pbkey:
            server_pb_key = pbkey.readline()
    except FileNotFoundError:
        print("please, edit name of private key file on string 40")
        exit()

    for user in usernames:
        # generating and writing new private and public keys
        pv_key, pb_key = generate_key(user)

        # making new user config
        new_user_config(user, pv_key, port, server_ip, server_pb_key, user_number)

        # adding new user to the main config
        add_to_main(pb_key, user_number, user, conf_name)

        user_number += 1

    os.system('systemctl restart wg-quick@wg0')

    print('Users successfully added, WireGuard restarted. To set WireGuard on their devices use users configs'
          ' or create rq-code via command below')
    print('qrencode -t ansiutf8 < {user}.conf')


if __name__ == "__main__":
    main()
