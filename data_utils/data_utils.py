# Required for sp_scraper
import requests
from bs4 import BeautifulSoup
import pandas as pd
import csv

# Required for url_scraper on top of some from sp_scraper
import re
from requests_futures.sessions import FuturesSession
from datetime import datetime

# Required for download_mp3s on top of url_scraper
import numpy as np
import urllib.request
import os
import warnings
warnings.filterwarnings("ignore")



def_page = "https://www.sangeethapriya.org/display_tracks.php"
def_url = "https://www.sangeethapriya.org/fetch_tracks.php?ragam"
cookie  = 'G_ENABLED_IDPS=google; _ga=GA1.2.1416645183.1618886299; G_AUTHUSER_H=0; sangeethamshare_login=arunravishankar%40gmail.com; _gid=GA1.2.589416232.1619580559; PHPSESSID=94sl2ikuaebethc0gu6t9vm0ud; _gat=1; sessiontime=1619866771; PHPSESSID=94sl2ikuaebethc0gu6t9vm0ud; sessiontime=1619866771'

headers = {
    'Connection': 'keep-alive',
    'Cache-Control': 'max-age=0',
    'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="90", "Google Chrome";v="90"',
    'sec-ch-ua-mobile': '?0',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    'Sec-Fetch-Site': 'same-origin',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-User': '?1',
    'Sec-Fetch-Dest': 'document',
    'Referer': 'https://www.sangeethamshare.org/login.php?url=%2Ftvg%2FUPLOADS-5201---5400%2F5268-V_Subramaniam%2F',
    'Accept-Language': 'en-US,en;q=0.9',
    'Cookie': 'G_ENABLED_IDPS=google; _ga=GA1.2.1416645183.1618886299; G_AUTHUSER_H=0; sangeethamshare_login=arunravishankar%40gmail.com; _gid=GA1.2.589416232.1619580559; PHPSESSID=94sl2ikuaebethc0gu6t9vm0ud; _gat=1; sessiontime=1619866771; PHPSESSID=94sl2ikuaebethc0gu6t9vm0ud; sessiontime=1619866771'
}


class spScraper():
    """
    This class has the methods required to scrape the meta-data from 
    of all the files in the Sangeethapriya website.
    args: None
    attributes: cookie -> cookie needed to access the website
                        README has details about cookie
                page -> url which displays all tracks
                url -> url that displays tracks based classified by ragam
    """
    def __init__(self, cookie, page = def_page, url = def_url):
        """
        Instantiates the sp_scraper with cookie, page and url
        """
        self.cookie = cookie
        self.page = page
        self.url = url
        return self

    def meta_data_scraper(self):
        """
        This function scrapes out the list of unique values of the
        meta-data of all the audio files that exist in the database of Sangeethapriya.org.
        The meta-data includes Concert ID, Track, Kriti, Ragam,
        Composer and Main Artist.
        args:
        returns: composers, ragams, kritis, artists, uploaders 
        """  
        
        page = requests.get(self.page)
        soup = BeautifulSoup(page.text, 'html.parser')

        dropdown_items = soup.select('option[value]')
        values = [item.get('value') for item in dropdown_items]
        text_values = [item.text for item in dropdown_items]
        box_indices = [i for i, x in enumerate(values) if x == ""]

        composers = values[box_indices[0]+1:box_indices[1]]
        ragams = values[box_indices[1]+1:box_indices[2]]
        kritis = values[box_indices[2]+1:box_indices[3]]
        artists = values[box_indices[3]+1:box_indices[4]]
        uploaders = text_values[box_indices[4]+1:]

        return(composers, ragams, kritis, artists, uploaders)

    def sangeethapriya_df(self, composers, ragams, kritis, artists, uploaders, savefile = 'df_sangeethapriya'):
        """
        This function goes through the pages of Sangeethapriya's database
        and scrapes out the specific meta-data for each of the tracks in their
        database
        args: composers, ragams, kritis, artists, uploaders
        These are the lists of unique values that are returned by the function
        sangeethapriya_meta_data_scraper
        savefile : name of file to save
        args:composers, ragams, kritis, artists, uploaders
        returns: None (saves a file as filename)
        """
        url = self.url
        ragams_tables_html = []
        for i in range(len(ragams)):
            ragams_tables_html.append(requests.post(url,{"FIELD_TYPE": ragams[i]}).text)
        
        output_rows = []
        for i in range(len(ragams)):
            soup = BeautifulSoup(ragams_tables_html[i])
            table = soup.find("table")
            for table_row in table.findAll('tr'):
                columns = table_row.findAll('td')
                output_row = []
                for column in columns:
                    output_row.append(column.text)
                output_rows.append(output_row)
                
        with open('{}.csv'.format(savefile), 'w') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerows(output_rows)
            
        return(savefile+'.csv')


class urlScraper():
    """
    Reads the file saved from sangeethapriya_scraper.py
    Obtains album hrefs for each of the files - this takes about 2 hours to run
    Cleans the df to remove those entries that do not contain an album page
    Saves that file as df_album_hrefs.csv
    Samples 100 tracks from all the ragams that contain more than 100 files in the database
    Parses through the album pages to obtain the download urls for each file
    Cleans the df to remove those entries that do not contain a download url
    Saves the df 
    """

    def __init__(self):
        """
        """
        return self

    def df_uploaders_album_ids(df):
        """
        Parses the Uploaders and Album IDs from the Concert IDs
        args: df - dataframe containing Concert ID, Track, Kriti, Ragam,
        Composer and Artist
        return : df - dataframe appended by uploaders and album_ids  
        """
        df['Uploader'] = df['Concert ID'].str.split('-').str[0].str.strip()
        df['Album ID'] = df['Concert ID'].str.split('-').str[1].str.strip().str.lower()
        return df

    def get_album_href_(response):
        """
        Gets the album urls for a file 
        by using the Concert ID and 
        Track number from the dataframe and scraping 
        Sangeethapriya.
        args: response - response from a futures request
        return: album_href
        """
        soup = BeautifulSoup(response.text, features = "html.parser")
        div_main = soup.find('div', {'id':'main'})
        if div_main is None:                # Error handling
            album_href = 'None'
        else: 
            if div_main.a is None:          #Error handling
                album_href = 'None'
            elif div_main.a['href'] is None:   # If no url exists
                album_href = 'None'
            else:
                album_href = div_main.a['href']
        return album_href

    def futures_albums(self, uploaders, album_ids, lim=2000):
        """
        Creates futures sessions to obtain the album hrefs
        for every file that exists in the Sangeethapriya
        database.
        args : uploaders
            : album_ids
        kwargs : lim - number of parallel futures sessions
        return : list of all album urls
        """
        
        session = FuturesSession()
        marker = 0
        lim = lim
        all_album_urls = []
        url = "https://www.sangeethapriya.org/locate_album.php"
        
        while(marker) < (min(len(uploaders)+lim-1, len(uploaders))):
            now = datetime.now()
            current_time = now.strftime("%H:%M:%S")
            print("Current Time =", current_time) # Takes about 90 minutes to run
            futures = []
            for i in range(marker, min(marker+lim, len(uploaders))):
                payload = "UPLOADER={}&CONCERT_ID={}".format(uploaders[i], album_ids[i])
                headers = {'Content-Type': 'application/x-www-form-urlencoded'}
                futures.append(session.post(url, headers = headers, data = payload))
            album_urls = [self.get_album_href_(f.result()) for f in futures]
            all_album_urls.extend(album_urls)
            marker=marker+lim
        return all_album_urls    

    def high_ragam_counts_sample(df, min_rag, samp):
        """
        Picking ragams that have at least min_rag number of 
        files in the database. This will remove rare ragams from
        the dataframe. The dataframe that is input is the one
        that contains no null entries in the Album hrefs.
        args: df - dataframe containing the Ragam
            : min_rag - number of tracks per ragam
            : samp - number of tracks to sample in a ragam
        return: None
        Saves : Saves a csv file with the dataframe of sampled tracks    
        """
        ragam_counts = df['Ragam'].value_counts()
        high_ragam_counts = ragam_counts[ragam_counts > min_rag]
        over_min_rag_df = df[df.groupby('Ragam')['Ragam'].transform('size')>min_rag]
        sample_df = over_min_rag_df[over_min_rag_df['Ragam']==list(high_ragam_counts.keys())[0]].sample(samp, random_state = 0)

        for i in range(1,len(high_ragam_counts)):
            sample_df = sample_df.append(over_min_rag_df[over_min_rag_df['Ragam']==list(high_ragam_counts.keys())[i]].sample(samp, random_state = 0))
            
        
        sample_df.to_csv('over{}ragams{}sample.csv'.format(min_rag,samp))
        return sample_df

    def get_url_download_(response, track_table):
        """
        Parses html page to obtain the download url for the right track
        Contains error handling to handle pages that don't contain
        download urls or where the pages don't exist
        args: response from the get request. 
            : track_table - the track number that needs to be parsed
        returns: download_url for the appropriate file
        """
        regex = '0?{}'.format(track_table)
        soup = BeautifulSoup(response.text, features = "html.parser")
        filelist_text = soup.find('ul',{'id':'filelist'})
        if filelist_text is None:
            return('None')
        else:
            if filelist_text.find_all('li', {'class':'audio'}) is None:
                return('None')
            else:
                filelist_files = filelist_text.find_all('li',{'class':'audio'})

                for item in filelist_files:
                    h2_text = item.find('h2').text
                    track_no = re.findall("\d+", h2_text)
                    if re.search(regex, track_no[0]) is None:
                        continue
                    else:
                        download_item = item.find('a',{'class':'download'})
                        start = str(download_item).find('http')
                        down_start_str = str(download_item)[start:]
                        end = down_start_str.find('\"')
                        return(str(download_item)[start:start + end])
        return('None')

    def download_urls(self, df, start = 0, end = 10, headers = headers):
        """
        Obtain downloads urls given the dataframe including the album hrefs
        args: df - dataframe containing album hrefs
            : start - start of df
            : end - end of df - default set to 10 - must use len(df)
            : headers - headers required to get the post requests
        returns: all_download_urls - list of all download urls
        """
        all_download_urls = []
        urls = list(df['Album hrefs'])
        tracks = list(df['Track'])

        for i in range(start, end):
            #Print the current time for every 50 urls obtained
            if i%50 ==0:
                now = datetime.now()
                current_time = str(now.strftime("%H:%M:%S"))
                print("{} Current Time = {}".format(i, current_time))
            payload = {}
            headers = headers
            url = urls[i]
            track = tracks[i]

            
            try:
                response = requests.request("GET", url, headers=headers, data=payload)
                if response.status_code == 200:
                    all_download_urls.append(self.get_url_download_(response, str(track)))
                else:
                    all_download_urls.append('None')
            except:
                all_download_urls.append('None')

        return all_download_urls

    def append_download_urls_save_df(df, download_urls, filename):
        """
        Appends a column to the df to include the download urls
        for each file
        """
        df['Download URLs'] = download_urls
        df.to_csv(filename, index=False)
        return

    def clean_no_null(df, column):
        """
        Removes the entries that do not have download_urls
        args: df
        returns: df
        """
        return(df[df[column] != 'None'])

    def run_obtain_album_hrefs(self, df_filename = 'df_sangeethapriya.csv', 
                                names = ["Concert ID","Track","Kriti","Ragam","Composer","Main Artist"],
                                album_href_savefile = 'df_album_hrefs.csv'):
        """
        """
        df = pd.read_csv(df_filename, names = names)
        df = self.df_uploaders_album_ids(df)
        df['Album hrefs'] = self.futures_albums(df['Uploader'], df['Album ID'], lim=2000)
        
        # Takes about 2 hours to run
        
        df = self.clean_no_null(df, 'Album hrefs')
        df = df.drop(['Uploader', 'Album ID'], axis=1)
        # These urls are not accessible because they have http:// instead of https:// - Let's change that
        album_hrefs = list(df['Album hrefs'])
        new_album_hrefs = ["https://www." + item[7:] + '/' for item in album_hrefs]
        df['Album hrefs'] = new_album_hrefs
        df.to_csv(album_href_savefile, index = False)
        # Maybe remove the return
        return(album_href_savefile)

    def run_download_urls(self,album_href_filename = 'df_album_hrefs.csv', min_rag = 100, samp = 100, samp_2 = 50):
        """
        """
        df = pd.read_csv(album_href_filename)
        df = self.high_ragam_counts_sample(df, min_rag, samp)
        df['Download URLs'] = self.download_urls(df, start = 0, end = len(df), headers = headers)

        # Takes about 8-9 hours to run
        df = self.clean_no_null(df, 'Download URLs')
        
        unique_ragams = list(df['Ragam'].unique())
        df_samp_2 = df[df['Ragam'] == unique_ragams[0]].sample(samp_2, random_state = 0)
        for i in range(1, len(unique_ragams)):
            df_samp_2 = df_samp_2.append(df[df['Ragam'] == unique_ragams[i]].sample(samp_2, random_state = 0))
        savefile = 'sample_min_rag_{}_samp_{}_{}_df.csv'.format(min_rag, samp, samp_2)
        df_samp_2 = df_samp_2.sample(frac=1, random_state = 0)
        df_samp_2.to_csv(savefile)

        return(savefile)


   ## Write rows to files instead of writing the whole file directly
    ## If I am running parallel downloads, I will need to write to a dictionary
    ## and then read from that.


class downloader():
    """
    This class has methods required to download the files from a dataframe
    that downloads the download_urls
    """
    def __init__(self, cookie = cookie):
        """
        """
        self.cookie = cookie
        return self

    def download_file_(self, url, filename, cookie):
        """
        Downloads a file given the url
        args: url, filename, cookie
        """
        opener = urllib.request.build_opener()
        opener.addheaders = [('Cookie', cookie)]
        urllib.request.install_opener(opener)
        urllib.request.urlretrieve(url, filename)
        file_size = os.path.getsize(filename)/1048576       # Size in MB
        #print("File Size is :", file_size, "MB")

        return(file_size)

    def download_files(self, df, workdir):
        """
        Downloads a file from the Sangeethapriya database,
        gets the features (chromagram and spectral centroid)
        """
        size = 0

        for index, row in df.iterrows():
            filename = os.path.join(workdir, 'song_' + str(index) + '.mp3')

            url = row['Download URLs']

            if index % 10 == 0:
                print(index, "Current Time =", datetime.now().strftime("%H:%M:%S"))

            now = datetime.now()
            try:
                size += self.download_file_(url, filename, cookie = self.cookie)
            except:
                continue

        return(size)


def main():
    # Data Scraping
    sp_scraper = spScraper()
    composers, ragams, kritis, artists, uploaders = sp_scraper.meta_data_scraper()
    sp_scraper.sangeethapriya_df(composers, ragams, kritis, artists, uploaders, 'df_sangeethapriya')

    # Download URL Scraping
    url_scraper = urlScraper()
    album_href_filename = url_scraper.run_obtain_album_hrefs()
    df_samp = url_scraper.run_download_urls(album_href_filename = album_href_filename, min_rag = 100, samp = 100, samp_2 = 50)

    # Download files
    cwd = os.getcwd()
    songs_dir = os.path.join(cwd, 'songs')
    begin_time = datetime.now()
    df = pd.read_csv(df_samp)
    dwnldr = downloader()
    size = dwnldr.download_files(df, songs_dir)
    print("Total time to process the files is :", datetime.now() - begin_time)
    print("Total data processed is :", size, "MB")
    # Have to handle errors in downloads
    return

if __name__ == '__main__':
    main()