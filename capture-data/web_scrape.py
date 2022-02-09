import os
import re
import json
import time
import pytz
import boto3
import pyowm
import urllib
import datetime
import requests
import pandas as pd
from bs4 import BeautifulSoup

s3 = boto3.client('s3')

##########################
# Gym scraping functions #
##########################

def get_occupancy_boulderwelt(gym_name:str, url: str) -> tuple():
    # make POST request to admin-ajax.php 
    req = requests.post(f"{url}/wp-admin/admin-ajax.php", data={"action": "cxo_get_crowd_indicator"})
    if req.status_code == 200:
        data = json.loads(req.text)
        if 'percent' in data:
            occupancy = int(data['percent'])
        elif 'level' in data:
            occupancy = int(data['level'])
        else:
            print(f"Response doesn't contain percent or level for occupancy. Response is: {req.text}")
            occupancy = 0

        # waiting system implemented
        if 'queue' in data and int(data['queue']) > 0:
            occupancy += int(data['queue']) / 10
        return occupancy
    
    # admin-ajax.php not working
    page = requests.get(url)
    if page.status_code != 200:
        return 0
    try:
        occupancy = int(float(re.search(r'style="margin-left:(.*?)%"', page.text).group(1)))
    except:
        occupancy = 0
    return occupancy

def get_occupancy_boulderado(gym_name:str, url: str) -> tuple():
    url_mappings = {
        'Magicmountain': 'https://www.boulderado.de/boulderadoweb/gym-clientcounter/index.php?mode=get&token=eyJhbGciOiJIUzI1NiIsICJ0eXAiOiJKV1QifQ.eyJjdXN0b21lciI6Ik1hZ2ljTW91bnRhaW4yMDIwMTQifQ.8919GglOcSMn9jl48zZVqNtZzXHh9RX23pN9F6DgX3E&ampel=1',
        'Burgoberbach': 'https://www.boulderado.de/boulderadoweb/gym-clientcounter/index.php?mode=get&token=eyJhbGciOiJIUzI1NiIsICJ0eXAiOiJKV1QifQ.eyJjdXN0b21lciI6IkJvdWxkZXJIYWxsIn0.jUG93IaTtWf--d7mPMuZ1wPkBvmXSm2MhhcKf6HQeMA&ampel=1',
        'Erlangen': 'https://www.boulderado.de/boulderadoweb/gym-clientcounter/index.php?mode=get&token=eyJhbGciOiJIUzI1NiIsICJ0eXAiOiJKV1QifQ.eyJjdXN0b21lciI6IlN0ZWluYm9ja0VybGFuZ2VuMzkyMDIxIn0.jchq4dpdvDPMWYXUEFRdeBCctqEJoIUIiC_6jvxFmSo&ampel=1',
        'Konstanz': 'https://www.boulderado.de/boulderadoweb/gym-clientcounter/index.php?mode=get&token=eyJhbGciOiJIUzI1NiIsICJ0eXAiOiJKV1QifQ.eyJjdXN0b21lciI6IlN0ZWluYm9ja0tvbnN0YW56MzkyMDE5In0.Io2pIXQ4lXUmRXM3Q0snudOGYytyZkVv3hbSh_QrUA0&ampel=1',
        'Nurnberg': 'https://www.boulderado.de/boulderadoweb/gym-clientcounter/index.php?mode=get&token=eyJhbGciOiJIUzI1NiIsICJ0eXAiOiJKV1QifQ.eyJjdXN0b21lciI6IlN0ZWluYm9ja05SQkcyMDIwMzkifQ.-HR_1FyjCV0NpmloWAeY5rMpzYke7VD-gcEf7z6xALI&ampel=1',
        'Passau': 'https://www.boulderado.de/boulderadoweb/gym-clientcounter/index.php?mode=get&token=eyJhbGciOiJIUzI1NiIsICJ0eXAiOiJKV1QifQ.eyJjdXN0b21lciI6IlN0ZWluYm9ja1Bhc3NhdTE3In0.jlrNfNWhp0xGk3YDJNN__j4rtMUKhd_B8sdi_93MThY&ampel=1',
        'Zirndorf': 'https://www.boulderado.de/boulderadoweb/gym-clientcounter/index.php?mode=get&token=eyJhbGciOiJIUzI1NiIsICJ0eXAiOiJKV1QifQ.eyJjdXN0b21lciI6Ilppcm5kb3JmIn0.JbdO230u8mmY0Oh5afF86yI3_sUwVmkPQiKfYpWwkOo&ampel=1'
    }
    # get corresponding link for gym
    for location in url_mappings:
        if location in gym_name:
            request_url = url_mappings[location]
            break
    else:
        return 0
    # obtain occupancy from url
    page = requests.get(request_url)
    if page.status_code != 200:
        return 0
    soup = BeautifulSoup(page.content, 'html.parser')
    try:
        occupancy = int(re.search(r'left: (\d*)%', str(soup.find_all("div", class_="pointer-image")[0]['style'])).group(1))
    except:
        occupancy = 0
    return occupancy

def get_occupancy_webclimber(gym_name:str, url: str) -> tuple():
    maps = {
        'Braunschweig': ['https://158.webclimber.de/de/trafficlight?callback=WebclimberTrafficlight.insertTrafficlight&key=yspPh6Mr2KdST3br8WC7X8p6BdETgmPn&hid=158&container=trafficlightContainer_1&type=2&area=1', #innen
                         'https://158.webclimber.de/de/trafficlight?callback=WebclimberTrafficlight.insertTrafficlight&key=yspPh6Mr2KdST3br8WC7X8p6BdETgmPn&hid=158&container=trafficlightContainer_2&type=2&area=2'], #draußen
        'Heavens': ['https://210.webclimber.de/de/trafficlight?callback=WebclimberTrafficlight.insertTrafficlight&key=b8cab21X5BEfm2g8zr32eX1kgfwg1EQx'],
        'Landshut': ['https://157.webclimber.de/de/trafficlight?callback=WebclimberTrafficlight.insertTrafficlight&key=CycEfe2pf8xmNfM39b63UeFcUz4ARsWP&hid=157&container=trafficlightContainer_1&type=2&area=1', # klettern
                     'https://157.webclimber.de/de/trafficlight?callback=WebclimberTrafficlight.insertTrafficlight&key=CycEfe2pf8xmNfM39b63UeFcUz4ARsWP&hid=157&container=trafficlightContainer_2&type=2&area=2', # bouldern
                     'https://157.webclimber.de/de/trafficlight?callback=WebclimberTrafficlight.insertTrafficlight&key=CycEfe2pf8xmNfM39b63UeFcUz4ARsWP&hid=157&container=trafficlightContainer_3&type=2&area=6'], # outdoors
        'Nurnberg climbing factory': ['https://173.webclimber.de/de/trafficlight?callback=WebclimberTrafficlight.insertTrafficlight&key=aHm2rs53fCs1H7F01dxDpeFZ5V3mKH8f&hid=173&container=trafficlightContainer&type=&area='],
        'Regensburg DAV': ['https://126.webclimber.de/de/trafficlight?callback=WebclimberTrafficlight.insertTrafficlight&key=THbq9w2DkUhmaKv7nvrXraeFQ8BSYf6C'],
        'Straubing': ['https://167.webclimber.de/de/trafficlight?key=9hwaBUT2G3PbrUQZ1xG3w4xCzvh98SN3'],
    }
    # get corresponding link for gym
    for key in maps:
        if key in gym_name:
            request_url = maps[key]
            break
    else:
        return 0
    
    occupancies = []
    for url in request_url:
        page = requests.get(url)
        if page.status_code != 200:
            return 0
        try:
            occupancy = re.findall(r'width: (.*)%', page.text)[0]
        except:
            occupancy = 0
        occupancies.append(occupancy)

    occupancy = '/'.join(occupancies)
    return occupancy


def get_occupancy_dav(gym_name:str, url: str) -> tuple():
    request_url = 'https://tickboard.de/public/pos_manager/CustomerEntries/getEntriesLeft'
    page = requests.get(request_url)
    if page.status_code != 200:
        return 0
    results = re.findall(r'<div class="sys-hall-title">(.*?)<\/div>.*?Klettern:.*?(\d*)%.*?Bouldern:.*?(\d*)%', page.text, re.DOTALL)
    for res in results:
        name, klettern, bouldern = res
        if name.replace('KB ', '') in gym_name:
            occupancy = bouldern + '/' + klettern
            break
    else:
        occupancy = 0
    return occupancy


def get_occupancy_hersbruck(gym_name:str, url: str) -> tuple():
    # found the request in the website's developer tools. this returns a long string. use regex
    request_url = 'https://www.boulderado.de/boulderadoweb/gym-clientcounter/index.php?mode=get&token=eyJhbGciOiJIUzI1NiIsICJ0eXAiOiJKV1QifQ.eyJjdXN0b21lciI6IkRBVkhlcnNicnVjayJ9.EdAisBKvuApVOGYnctB9C-LZ2c3gu5kWp6CnzQPQgAk&amp'
    page = requests.get(request_url)
    if page.status_code != 200:
        return 0
    try:
        besucher, frei = re.findall(r'<span data-value="(\d*)?"', page.text)
        occupancy = int(int(besucher) * 100 / int(frei))
    except:
        occupancy = 0
    return occupancy


def get_occupancy_erlangen_dav(gym_name:str, url: str) -> tuple():
    # found the request in the website's developer tools. this returns a long string. use regex
    request_url = 'https://www.boulderado.de/boulderadoweb/gym-clientcounter/index.php?mode=get&token=eyJhbGciOiJIUzI1NiIsICJ0eXAiOiJKV1QifQ.eyJjdXN0b21lciI6IkRBVkVybGFuZ2VuMjMyMDIwIn0.Fr3KR0obdp_aYzCIclQTMZr0dVIxT0bfyUVODU_u64M'
    page = requests.get(request_url)
    if page.status_code != 200:
        return 0
    try:
        besucher, frei = re.findall(r'<span data-value="(\d*)?"', page.text)
        occupancy = int(int(besucher) * 100 / int(frei))
    except:
        occupancy = 0
    return occupancy


def get_occupancy_einstein(gym_name:str, url: str) -> tuple():
    with requests.Session() as session:
        page = session.get(url)
        if page.status_code != 200:
            return 0, 0
        soup = BeautifulSoup(page.content, 'html.parser')
        try:
            # to obtain info under #document in html https://stackoverflow.com/a/42953046/4569908
            frame = soup.select("iframe")[0]
            frame_url = urllib.parse.urljoin(url, frame["src"])
            response = session.get(frame_url)
            frame_soup = BeautifulSoup(response.content, 'html.parser') 
            occupancy = re.search(r'left: (\d+)%', str(frame_soup)).group(1)
        except:
            occupancy = 0
    return occupancy

####################################

def get_weather_info(location: str) -> tuple():
    '''
    Get weather temperature and status for a specific location
    '''
    temp = 0
    status = ''
    for i in range(5):
        try:
            mgr = pyowm.OWM(os.environ['OWM_API']).weather_manager()
            observation = mgr.weather_at_place(location).weather
            temp = int(round(observation.temperature('celsius')['temp']))
            status = observation.status
            break
        except:
            print(f"try i={i}/5. PYOWM gives timeout error at location: {location}")
        time.sleep(5)
    return temp, status


def scrape_websites(current_time: str, gymdatadf: pd.DataFrame) -> pd.DataFrame:
    webdata = []
    for gym_name, gym_data in gymdatadf.items():
        weather_temp, weather_status = get_weather_info(gym_data['location'])
        # string -> callable function https://stackoverflow.com/a/22021058/4569908
        scrape_data = globals()[gym_data['function']]
        occupancy = scrape_data(gym_name, gym_data['url'])
        print(f"{gym_name}: occupancy={occupancy}, temp={weather_temp}, status={weather_status}")
        if occupancy == 0:
            continue
        webdata.append((current_time, gym_name, occupancy, weather_temp, weather_status))
  
    webdf = pd.DataFrame(data=webdata, columns=['time', 'gym_name', 'occupancy', 'weather_temp', 'weather_status'])
    return webdf


def get_current_time():
    # https://stackoverflow.com/a/60169568/4569908
    dt = datetime.datetime.now()
    timeZone = pytz.timezone("Europe/Berlin")
    aware_dt = timeZone.localize(dt)
    if aware_dt.dst() != datetime.timedelta(0,0):
        #summer time
        dt += datetime.timedelta(hours=2)
    else:
        #winter time
        dt += datetime.timedelta(hours=1)
    dt = dt.strftime("%Y/%m/%d %H:%M")

    #round to the nearest 20min interval
    minutes = [0, 20, 40]
    current_min = int(dt.split(':')[1])
    distances = [abs(current_min - _min) for _min in minutes]
    closest_min = minutes[distances.index(min(distances))]
    current_time = dt.replace(':'+str(current_min), ':'+str(closest_min))

    return current_time


def lambda_handler(event, context):

    current_time = get_current_time()
    current_time_hh_mm = datetime.datetime.strptime(current_time, '%Y/%m/%d %H:%M').strftime("%H:%M")

    if current_time_hh_mm < '07:00' or current_time_hh_mm > '23:00':
        print("Scraping outside of opening hours, skipping")
        return

    # download gym data from S3
    s3.download_file(os.environ['BUCKETNAME'], os.environ['GYMDATANAME'], f"/tmp/{os.environ['GYMDATANAME']}")
    gymdatadf = pd.read_json(f"/tmp/{os.environ['GYMDATANAME']}")
    
    print(f"Current time: {current_time}")
    webdf = scrape_websites(current_time, gymdatadf)

    # only update if occupancy in gyms is > 0
    if webdf.empty:
        print("Nothing was scraped, S3 is not updated")
        return

    # download dataset from S3
    dfpath = f"/tmp/{os.environ['CSVNAME']}"
    s3.download_file(os.environ['BUCKETNAME'], os.environ['CSVNAME'], dfpath)

    # merge boulderdata with tmp file
    webdf.append(pd.read_csv(dfpath)).to_csv(dfpath, index=False)

    # upload dataset to S3
    s3.upload_file(dfpath, os.environ['BUCKETNAME'], os.environ['CSVNAME'])
    print("Scraping done and data updated to S3")
    return
