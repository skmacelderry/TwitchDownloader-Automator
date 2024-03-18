import sys
import subprocess
import json
import requests
import re
import asyncio
import promptlib
from math import ceil
from datetime import datetime
from playwright.async_api import async_playwright
from time import perf_counter

class Clip:
    def __init__(self, data, link):
        self.data = data  # contains 'streamer', 'title', 'date', and 'duration'
        self.link = link  # original clip link
        self.vod_data = {'ID': '', 'start': 0, 'end': 0}
        self.vod_link = ''  # this breaks when part of the dict, for some reason


def print_program_header():
    title = "TwitchDownloader Automator"
    author = "Written by hylight"
    print("=" * 60, f"\n{title:^60}", f"\n{author:^60}\n", "=" * 60)


def sanitize_name(file_name):
    # invalid characters: < > : " / \ | ? * NULL characters (0x00-0x1F) and DEL (0x7F)
    invalid_chars = r'[<>:"/\\|?*\x00-\x1F\x7F]'

    # replace invalid characters & spaces with underscores
    sanitized_name = re.sub(invalid_chars, '_', file_name)
    sanitized_name = sanitized_name.replace(' ', '_')

    return sanitized_name


def duration_to_seconds(duration):
    # expected format: --h--m--s
    parts = duration.split('h')
    hours = int(parts[0]) if parts[0] else 0

    parts = parts[1].split('m')
    minutes = int(parts[0]) if parts[0] else 0

    parts = parts[1].split('s')
    seconds = int(parts[0]) if parts[0] else 0

    total_seconds = hours * 3600 + minutes * 60 + seconds
    return total_seconds


def seconds_to_duration(seconds):
    seconds = seconds % (24 * 3600)
    hours = seconds // 3600
    seconds %= 3600
    minutes = seconds // 60
    seconds %= 60

    duration = ''
    if hours > 0:
        duration += f"{int(hours)}h"
    if minutes > 0 or hours > 0:
        duration += f"{int(minutes):02}m"
    if seconds > 0 or minutes > 0 or hours > 0:
        duration += f"{int(seconds):02}s"

    return duration


def main():

    prompter = promptlib.Files()    # for displaying file explorer prompt
    tt_s = perf_counter()   # for getting program runtime
    input_path = ''
    index = 0
    url_list = []    # list of original links used
    clip_list = []   # list of Clip objects

    print_program_header()

    print('\nSelect a text file with your clip links.')

    input_path = prompter.file()
    file_name = input_path[input_path.rfind("\\") + 1:]
    print(file_name)

    try:
        with open(file_name, 'r') as file:
            for line in file:
                url_list.append(line.strip())
    except FileNotFoundError:
        print("Error, file not found:", file_name)
        sys.exit(1)

    print('Select the directory where TwitchDownloaderCLI and FFmpeg are downloaded.')
    client_dir = prompter.dir() + '\\'
    print(client_dir)
    print('Select desired directory to save clips: ')
    output_path = prompter.dir() + '\\'
    print(output_path)
    print('Select desired directory to save chat: ')
    json_path = prompter.dir() + '\\'
    print(json_path)

    client_id = input('Enter your Twitch Developer App client ID: ')
    auth = input('Enter your Twitch Developer App client token: ')
    auth = 'bdo3lcxr8lgvwpj2yp1jmc1rmbxqet'
    client_id = 'afjotvcdonn5bue5s0a9d7wb022dld'

    url = ''
    params = {}
    headers = {
        'Authorization': f'Bearer {auth}',
        'Client-Id': f'{client_id}'
    }

    print("\nDownloading clips...\n")

    for entry in url_list:
        # gets the ID from the original url for request
        clip_id = entry[entry.rfind("/") + 1:]

        url = "https://api.twitch.tv/helix/clips?id=" + clip_id
        # get request for clip metadata
        response = requests.get(url, params=params, headers=headers)

        if response.status_code == 200:
            output = json.loads(response.text)
            metadata = {}
            # parsing response data into new dictionary
            for item in output['data']:
                metadata['streamer'] = item['broadcaster_name']
                metadata['title'] = sanitize_name(item['title'])
                time = datetime.strptime(item['created_at'], "%Y-%m-%dT%H:%M:%SZ")
                metadata['date'] = time.strftime("[%#m-%#d-%y]")
                metadata['duration'] = ceil(item['duration'])
            clip_list.append(Clip(metadata, entry))
        else:
            print(f"Error: {response.status_code}")

        # see TwitchDownloader github page for formatting guidelines if changes desired

        file_name = clip_list[index].data['date'] + '-' + clip_list[index].data['streamer'] + '-' + clip_list[index].data['title']
        command = 'TwitchDownloaderCLI.exe clipdownload -u ' + entry + ' -o ' + output_path + file_name + '.mp4'

        index += 1
        print('\nExecuting: ', command)

        subprocess.run(f"cd /d {client_dir} && {command}", shell=True)

    index = 0
    # by using a clip link to access the full vod, you can get the vod url and start time together
    # -opens a twitch link in the background, and navigates to 'watch full vod' for chat link
    async def pw_main(index):
        async with async_playwright() as p:
            # depending on which url a twitch clip has, the site format changes!
            # -uncomment version as needed
            browser = await p.firefox.launch()
            page = await browser.new_page()
            await page.goto(str(url_list[index]))
            # use if from clips.twitch.tv/
            await page.get_by_label("Clip dropdown options").click()
            await page.get_by_label("Watch full video dropdown item").click(timeout=60000)
            # use if from www.twitch.tv/.../clips/
            # await page.get_by_role("link", name="Watch Full Video").click(timeout=60000)
            print(page.url)
            clip_list[index].vod_link = page.url
        # ---------------------
        await browser.close()
        await asyncio.sleep(1)

    print('\n\nGetting vod links...\n')

    for entry in url_list:
        asyncio.run(pw_main(index))
        index += 1

    print("\nGetting chat...")

    index = 0
    # for chat you need vod link -> start/end times -> render preferences
    for entry in clip_list:
        # parsing for ID and start time
        vod_id = entry.vod_link[entry.vod_link.rfind('/') + 1:entry.vod_link.rfind('?')]
        clip_list[index].vod_data['ID'] = vod_id
        clip_list[index].vod_data['start'] = entry.vod_link[entry.vod_link.rfind('=') + 1:]

        # TwitchDownloader CLI expects seconds for start/end, so times needs to be converted and calculated
        clip_list[index].vod_data['start'] = duration_to_seconds(clip_list[index].vod_data['start'])
        clip_list[index].vod_data['end'] = clip_list[index].vod_data['start'] + clip_list[index].data['duration'] + 1
        clip_list[index].vod_data['start'] -= 30

        start_and_end = str(clip_list[index].vod_data['start']) + ' -e ' + str(clip_list[index].vod_data['end'])

        file_name = clip_list[index].data['date'] + '-' + clip_list[index].data['streamer'] + '-' + clip_list[index].data['title']

        command = 'TwitchDownloaderCLI.exe chatdownload --id ' + clip_list[index].vod_data['ID'] + ' -b ' + \
            start_and_end + ' -o ' + json_path + file_name + '-[chat].json'

        print('\nExecuting: ', command)
        subprocess.run(f"cd /d {client_dir} && {command}", shell=True)

        command = 'TwitchDownloaderCLI.exe chatrender -i ' + json_path + file_name + \
            '-[chat].json -h 1200 -w 700 --framerate 60 -f Arial --font-size 24 -o D:\\Editing\\Twitch\\chat\\' + \
            file_name + "-[chat].mp4"

        print('\n\nExecuting: ', command)
        subprocess.run(f"cd /d {client_dir} && {command}", shell=True)
        index += 1

    tt_e = perf_counter()
    steamhappy = """
                                                                                                        
                                                       ..........                                   
                                                    :..............                                 
                                   .........      ...................                               
                                ...............:*-.....................                             
                             -..................:-+:..++...*#-..........                            
                            ............::.........=#@@@:.-@@@%:........                            
                           :............@@@@@+......*@@@@@@@@@@#.........                           
                           .........#%=.+@@@@@@=.....%@@@@@@@@@*........                            
                          %-........@@@@@@@@@@@@:....*@@@@@@@@+........+%                           
                        %%#-........#@@@@@@@@@@%.....-*@@@@%-.........:-=##                         
                      %##---:........=@@@@@@@@*:....:=..............:------##                       
                     %#------:..........-==-:......:+.............:-=----:---#%                     
                   %%*--------=--==-:.............:---:......::--------------:+#%                   
                  %%=:--:::::--------=#%+:.....:-----------------=+=------------#%                  
                 %#=::------------------*@*=+*#########%%#**+==*#-::-------------*#                 
                %#+-::----------------:--#@@%.............+@@@@%::::--------------+#%               
         #%###%%%*:------------------:::=@@@@@+#@@@+:::-*@@@@@@@-:::---------------+#%%#####        
        *#+:---=+---------------=====+%@@@@@@@@@@@@@@@@@@@@@@@@@@%+===--------------*########       
        *#+::::-------------------::-+@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@-----------------#######        
         #%=:-----------------------:+@@@@@@@@@@@@@@@@@@@@@@@@@@@@@%-----------------+#####         
          %%*------------------------*@@@@@@@@@@@@@@@@@@@@@@@@@@@@@=------------------###%          
           %##+----------------------+@@@@@@@@@@@@@@@@@@@@@@@@@@@@@-------------------*#            
             %%*---------------------+@@@@@@@@@@@@@@@@@@@@@@@@@@@@+-------------------*#            
              #*----------------------@@@@@@@%##%@@@@@@@@@@@@@@@@%--------------------+#            
              ##----------------------%@@@@#+++++++++++%@@@@@@@@@=--------------------*#            
              %#=---------------------#@@@*++++++++++++++%@@@@@@+---------------------##            
               #*---------------------=@@*++++++++++++++++%@@@@#---------------------=##            
               %#----------------------#%++++++++++++++++++@@@%----------------------*#%            
                ##---------------------=#=+++++++++++++++++*@%----------------------=#%             
                 #*---------------------+=.-++++++++++++++++*-----------------------#%              
                 %##---------------------+*:++++++++++++++*+-----------------------##%              
                   ##=--------------------=#*++=-..:-:..+#=-----------------------##                
                    %%*=--------------------=%#-:...:-**=-----------------------+##                 
                      %%*==--===================++*+====-===================--=##%                  
                        %%#=================================================+##%                    
                           %%#+==========================================+#%%                       
                              %%%#*==================================*####                          
                                  %%####*===================++**#####%                              
                                        ##+======*%%##########%                                     
                                         ##*====+#% #########%                                      
                                           %#####%   %#####%                                        
    """
    print(steamhappy)

    print('\nTotal runtime: ', seconds_to_duration(tt_e - tt_s), 'seconds', '\n\nExiting program...\n')


if __name__ == '__main__':
    main()
