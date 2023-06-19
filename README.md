# geolokapp
A python script put together when collecting threat data from Abuse.ch, enabling extraction of the IP(v4 as of now) addresses to get fresh GeoIP-lookup data from Maxmind´s Geolite2 db. 
Taking baby steps in Python, i tried to make functions more generic why the ip-extraction and geoip-lookup functions are separated from main script.

Input:
- .csv or .json(list of dictionaries or dictionary of list of dictionaries)

Output:
- .csv-format of either the original dataframe, the GeoIP-data, both separately or combined, and/or a .txt with the extracted IP addresses.

Requirements:

- GeoLite2-City.mmdb and GeoLite2-ASN.mmdb installed
- An AccountID and Licence key(free) from Maxmind.com
- geoipupdate from https://github.com/maxmind/geoipupdate

As intention is automation, not much of user interactivity is to expect but filtering a chosen column could be done and initial check of the table structure. No error handling to speak of yet. 

Example usage:

"$python3 geolokapp.py /home/strfjmpr/ipblocklist.json -c ip_address -e c -f country -d SE" would read the file ipblocklist.json into a dataframe, extract the IP addresses from named column "ip_address"(even if it is mixed with other data in cell), filter column "country" for "SE", do a GeoIP lookup on extracted IPs and export a combined dataframe in .csv format.
