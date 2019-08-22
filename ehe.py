#!/usr/bin/env python3

from bs4 import BeautifulSoup
from pertanggalan import generate_n_days_from_today
import requests
import pandas as pd
import time
import os
import random
from datetime import date


USER_AGENTS = open('user_agent.txt').read().splitlines()
headers = {
    'User-Agent': f'{random.choice(USER_AGENTS)}'}
df = pd.DataFrame()
FILE_NAME = date.today().strftime("%Y-%m-%d")


class Link():
    def __init__(self, list_of_date, sumber, pagination=50):
        self.pagination = pagination
        self.list_of_date = list_of_date
        self.sumber = sumber
        if not os.path.exists('csv/') and not os.path.exists('json/'):
            os.makedirs('csv/')
            os.makedirs('json/')

    def masukkan_link_ke_df(self, list_of_links):
        """ unpack list of list the returns it as a df, depends on sumber news """
        if type(list_of_links[0]) is not 'list': 
            print('not a list ')
            raise ValueError
        else: 
            list_of_links = [l for item in list_of_links for l in item]
        list_of_dicts = []
        for link in list_of_links:
            kumpulan_info = {}
            kumpulan_info['links'] = link
            kumpulan_info['sumber'] = self.sumber
            list_of_dicts.append(kumpulan_info)
        df = pd.DataFrame(list_of_dicts)
        return df

    def pull_link_bisnis(self):
        list_of_links = []
        for current_date in self.list_of_date:
            current_date = current_date.strftime('%d+%B+%Y')
            for j in range(self.pagination+1):
                kumpulan_info = {}
                link = f'https://www.bisnis.com/index?c=5&d={current_date}&per_page={j}'
                print(link)
                req = requests.get(link, headers=headers)
                soup = BeautifulSoup(req.content, 'lxml')
                box = soup.find('ul', class_='l-style-none')
                if box.find('h2') is not None:
                    print('no more berita')
                    break
                links = list(
                    set([a['href'] for a in box.find_all('a') if len(a['href'] > 55)]))
                list_of_links.append(links)
        return self.masukkan_link_ke_df(list_of_links)

    def pull_link_tempo(self):
        # https://www.tempo.co/indeks/2019/08/13
        list_of_links = []
        for current_date in self.list_of_date:
            current_date = current_date.strftime('%Y/%m/%d')
            link = f'https://www.tempo.co/indeks/{current_date}'
            req = requests.get(link)
            soup = BeautifulSoup(req.content, 'lxml')
            box = soup.find('ul', class_='wrapper')
            links = list(set([a['href'] for a in box.find_all('a')]))
            list_of_links.append(links)
        return self.masukkan_link_ke_df(list_of_links)

    def pull_link_detik(self):
        # https://news.detik.com/indeks/all/{page_number}?date={08}}/{month}/{year}}
        list_of_links = []
        for current_date in self.list_of_date:
            d, m, y = current_date.strftime('%d'), current_date.strftime(
                '%m'), current_date.strftime('%Y')
            for page_number in range(self.pagination+1):
                try:
                    link = f'https://news.detik.com/indeks/all/{page_number}?date={d}/{m}/{y}'
                    print(link)
                    header = {
                        'User-Agent': f'{random.choice(USER_AGENTS)}'}
                    req = requests.get(link)
                    soup = BeautifulSoup(req.content, 'lxml')
                    box = soup.find('ul', {'id': 'indeks-container'})
                    links = list(set([a['href'] for a in box.find_all('a')]))
                    list_of_links.append(links)

                except Exception as e:
                    print('error', str(e))
        return self.masukkan_link_ke_df(list_of_links)

    def pull_link_kompas(self):
        list_of_links = []
        for date_current in self.list_of_date:
            for j in range(1, self.pagination):
                url = f'https://indeks.kompas.com/all/{str(date_current)}/{j}'
                print(url)
                headers = {'User-Agent': f'{random.choice(USER_AGENTS)}'}
                req = requests.get(url, headers=headers)
                soup = BeautifulSoup(req.content, 'lxml')
                if soup.find('a', class_='article__link'):
                    pass
                else:
                    print('halaman terakhir')
                    break
                box = soup.find('div', class_='latest--indeks mt2 clearfix')
                links = list(set([a['href']
                                  for a in box.find_all('a')]))
                list_of_links.append(links)
        return self.masukkan_link_ke_df(list_of_dict)

    def run(self):
        if self.sumber.lower() == 'kompas':
            return self.pull_link_kompas()
        elif self.sumber.lower() == 'detik':
            return self.pull_link_detik()
        elif self.sumber.lower() == 'tempo':
            return self.pull_link_tempo
        elif self.sumber.lower() == 'bisnis':
            return self.pull_link_bisnis()
        else:
            print('sumber tidak jelas, dick stuck.')


def pull_paragraf_bisnis(link=None):
    r = requests.get(link)
    soup = BeautifulSoup(r.content, 'lxml')
    box = soup.find('div', class_='col-sm-10')
    return " ".join([p.text for p in box.find_all('p') if 'simak berita' not in p.text.lower()])


def pull_paragraf_kompas(link=None):
    headers = {'User-Agent': f'{random.choice(USER_AGENTS)}'}
    r = requests.get(link, headers=headers)
    s = BeautifulSoup(r.content, 'lxml')
    reader = s.find('div', {'class': 'read__content'})
    if 'MAAF KAMI TIDAK MENEMUKAN HALAMAN YANG ANDA CARI' in s.text:
        return '404'
    elif type(reader) == type(None):
        reader = s.find('div', {'class': 'main-artikel-paragraf'})
    elif 'jeo' in link:
        print('jeo link')
        return 'JEO TYPED SHIT'
    else:
        for child in reader.find_all("strong"):
            child.decompose()
    return(reader.get_text())


def remove_punctuation(kata):
    return kata.translate(None, string.punctuation)


def df_cleaner(path_to_csv, kasih_judul=False):
    df = pd.read_csv(path_to_csv)
    if not kasih_judul:
        df = df.drop([x for x in df.columns if 'Unnamed' in x], axis=1)

        df.to_csv(path_to_csv)
    else:
        df = df.drop([x for x in df.columns if 'Unnamed' in x], axis=1)

        print(df.head())
        print(f'terdapat {df.columns} sebagai judul')
        judul = [input(f'judul ke-{x}: \n>') for x in range(len(df.columns))]
        df.columns = judul
        df.to_csv(path_to_csv, index=False)
    df = df.drop([x for x in df.columns if 'Unnamed' in x], axis=1)
    return df
