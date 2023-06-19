#!/usr/bin/env python

"""Geolokapp.py: 
- Basic IP extraction and locally processed GeoIP lookup (Geolite2 db)
- Also extracts IPv4 addresses from columns that store more data than the addresses.
- Accepts input in comma separated .csv or .json structured as lists of dictionaries or dictionary of list of dictionaries.
- Mainly intended for non-interactive use.
- Options to export original data with GeoIP added, GeoIP data or only extracted IP addreses.
- Supports minimal column filtering
- In obvious need of improvements
"""
__author__      = "StrafeJumper"
__copyright__   = "Copyright 2023, Earth"
__license__ = "GPL v.3"
__version__ = "0.1.0"
__status__ = "In flux"


import pandas as pd
import numpy as np
import os,json,csv,re,argparse,configparser,sys,traceback
from datetime import datetime
import geoip2.database



config = configparser.ConfigParser()
config_path = 'config.ini'

if not os.path.exists(config_path):
    db_path = input("No config.ini file found. Please enter the path to the database files: ")
    config['DEFAULT'] = {'db_path': db_path}
    with open(config_path, 'w') as configfile:
        config.write(configfile)
else:
    config.read(config_path)
    db_path = config.get('DEFAULT', 'db_path', fallback=None)
    if db_path is None or not os.path.exists(db_path):
        db_path = input("No database path info in config.ini. Please enter path: ")
        config['DEFAULT'] = {'db_path': db_path}
        with open(config_path, 'w') as configfile:
            config.write(configfile)

def export_dataframe(dataframe, filename, suffix, output_path=None):
    timestamp = datetime.now().strftime("%y%m%d_%H%M%S")
    export_filename = f"{filename}_{suffix}_{timestamp}.csv"
    
    if output_path:
        export_filepath = os.path.join(output_path, export_filename)
    else:
        export_filepath = export_filename
        
    dataframe.to_csv(export_filepath, index=False)
    print(f"Exported dataframe to {export_filepath}")

parser = argparse.ArgumentParser()
parser.add_argument('file', help='File name')
parser.add_argument('-c', '--column', help='IP column', required=False)  
parser.add_argument('-e', '--export', nargs='+', help='Exports file, accepts "i" for IP-addresses, "g" for GeoIP-data, and "c" for GeoIP-data combined with input data', choices=['i', 'g', 'c'], required=False)
parser.add_argument('-o', '--output_path', help='Output path for exported files')
parser.add_argument('-f', '--filter_column', help='Filter for named column')
parser.add_argument('-d', '--filter_data', help='Filter data')
args = parser.parse_args()

file_name = args.file
ip_column = args.column
output_path = args.output_path
export_option = args.export
filter_column = args.filter_column
filter_data = args.filter_data

def extract_ip_address(text):
    ip_pattern = r"\b(?:\d{1,3}\.){3}\d{1,3}\b"
    ip_addresses = re.findall(ip_pattern, text)

    valid_ips = []
    for address in ip_addresses:
        try:
            ip_obj = ipaddress.IPv4Address(address)
            valid_ips.append(str(ip_obj))
        except ipaddress.AddressValueError:
            pass

    return valid_ips  # return a list of valid IPs, or empty list.

def geolite_lookup(ip_address):
    result = []
    # If single IP is provided as string, convert it to list
    if isinstance(ip_address, str):
        ip_address = [ip_address]
        
    for ip in ip_address:
        try:
            city_response = city_reader.city(ip)
            asn_response = asn_reader.asn(ip)
            result.append({'IP': ip, 'Country': city_response.country.iso_code, 
                           'City': city_response.city.name, 
                           'Postal Code': city_response.postal.code, 
                           'ASN': asn_response.autonomous_system_number, 
                           'Organization': asn_response.autonomous_system_organization})
        except Exception as e:
            print(f"Error processing {ip}: {e}")

    return pd.DataFrame(result)

try:

    if file_name.endswith('.json'):
        with open(file_name, 'r') as f:
            data = json.load(f)

        if isinstance(data, list):
            df = pd.DataFrame(data)

        elif isinstance(data, dict):
            df_list = []
            for key, values in data.items():
                temp_df = pd.DataFrame(values)
                temp_df['key'] = key  # Add key as a column
                df_list.append(temp_df)
            df = pd.concat(df_list)
        else:
            print("Unsupported JSON structure")
    elif file_name.endswith('.csv'):
        df = pd.read_csv(file_name, dtype={ip_column: str} if ip_column else str)
    else:
        print("Unsupported file type")
        
    if filter_column:
        if filter_data:
            df = df[df[filter_column] == filter_data]
            print(df)
        else:
            print("No column data provided, proceeding without filters.")
    else:
        print("COLUMN NAMES:")
        for column in df.columns:
            print(column)
        print("SAMPLE CONTENTS:")
        print(df.iloc[[1,2,3]])

    if ip_column is None:
        print("GeoIP lookups and export data requirs use of -c. Exiting.")
        exit()

    city_reader = geoip2.database.Reader(os.path.join(db_path, 'GeoLite2-City.mmdb')) 
    asn_reader = geoip2.database.Reader(os.path.join(db_path, 'GeoLite2-ASN.mmdb'))


    def extract_ip(s):
        pattern = r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'
        ip = re.findall(pattern, s)
        return ip[0] if ip else None

    def lookup(ip):
        ip = extract_ip(ip) if pd.notna(ip) else None
        if ip is not None:
            result = geolite_lookup(ip)
            if not result.empty:
                return result.iloc[0]
            else:
                return pd.Series([np.nan]*6, index=['Country', 'City', 'Postal Code', 'ASN', 'Organization', 'IP'])
        else:
            return pd.Series([np.nan]*6, index=['Country', 'City', 'Postal Code', 'ASN', 'Organization', 'IP'])

    df_geo = df[ip_column].apply(lookup)
    df_combined = pd.concat([df, df_geo], axis=1)
    df_ip_extract = df[ip_column].apply(extract_ip)

    if export_option:
        for option in export_option:
            if option == 'i':
                export_dataframe(df_ip_extract, file_name, "ip_addresses", output_path=output_path)
            elif option == 'g':
                export_dataframe(df_geo, file_name, "geo", output_path=output_path)
            elif option == 'c':
                export_dataframe(df_combined, file_name, "combined", output_path=output_path)
            
except Exception as e:
    print(f"An error occurred: {str(e)}")
    print("Traceback (most recent call last):")
    traceback.print_tb(e.__traceback__)
    sys.exit(1)
