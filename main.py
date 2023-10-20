import os.path
import time
import requests
from bs4 import BeautifulSoup
import bs4.element
import csv
import datetime
import hashlib
from loguru import logger


CSV_COL_NAME = ['title', 'link', 'date']


class ByBitParser:
    user_agent = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/116.0.5845.888 YaBrowser/23.9.2.888 Yowser/2.5 Safari/537.36')

    def __init__(self):
        self.__domain = 'https://announcements.bybit.com'
        self.__uri = f'{self.__domain}/en-US/'
        self.session = requests.session()
        self.session.headers['User-Agent'] = self.user_agent

    def __setattr__(self, key, value):
        object.__setattr__(self, key, value)
        if key == 'user_agent':  # При изменении свойства 'user_agent' он должен изменяться и в заголовках сессии
            self.session.headers['User-Agent'] = value

    @staticmethod
    def __parse_news_page(response: requests.Response) -> bs4.element.ResultSet:
        """
        На вход получает ответ сервера, находит все новости и возвращает их
        """
        soup = BeautifulSoup(response.text, 'lxml')
        news_block = soup.find('div', class_='article-list')  # Блок с новостями
        return news_block.find_all('a', class_="no-style")  # Все новости

    def __preprocess_news(self, news: list[bs4.element.Tag]) -> list[dict]:
        return [{
            CSV_COL_NAME[0]: item.find('span').text,
            CSV_COL_NAME[1]: self.__domain + item['href'],
            CSV_COL_NAME[2]: datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        } for item in news]

    def start(self, category: str = '', page: int = 1) -> list[dict]:
        response = self.session.get(url=self.__uri + f'?category={category}&page={page}')
        news = self.__parse_news_page(response)

        # Если новость НЕ в топе. На сайте есть закрепленные новости, все новые новости появляются под ними.
        news = [item for item in news if not item.find('div', class_='article-item-tag-top')]

        preprocessed_news = self.__preprocess_news(news)
        return preprocessed_news


def save_to_csv(lines: list[dict], filename: str, mode: str = "w"):
    with open(filename, mode, encoding='utf-8') as file:
        file_writer = csv.DictWriter(file, delimiter=",", lineterminator="\r", fieldnames=CSV_COL_NAME)
        if mode == 'w':  # Запись заголовков, если файл пустой
            file_writer.writeheader()
        file_writer.writerows(lines)


def filter_news(news: list[dict], last_news_hash: str) -> list[dict]:
    """
    Фильтрует новости.

    Идем от станых новостей к новым.
    Если увидим последнюю сохраненную новость, то берем все до после нее (в перевернутом списке).
    Если же мы не нашли последнюю сохраненную новость, то добавляем все.
    """
    i = len(news)
    for item in reversed(news):
        byte_news = bytes(item['title'], 'utf-8')
        i -= 1
        if hashlib.md5(byte_news).hexdigest() == last_news_hash:
            break
    else:
        return news[:]
    return news[:i]


def main(filename: str, category: str = '', page: int = 1):
    parser = ByBitParser()

    # Хеш последней новости. Если что-то пойдет не так, скпипт можно будет перезапустить без дублирования новостей
    last_news_hash = ''

    if not os.path.exists(filename):  # Создание файла, если его нет.
        save_to_csv([], filename)

    while True:
        news = parser.start(category, page)
        latest_news = filter_news(news, last_news_hash)

        if latest_news:
            save_to_csv(latest_news, filename, mode='a')

            # Обновление хэша последней новости
            byte_news = bytes(latest_news[0]['title'], 'utf-8')
            last_news_hash = hashlib.md5(byte_news).hexdigest()

            logger.success(f'В файл {filename} добавлено еще {len(latest_news)} свежих новостей. '
                           f'Последняя новость имеет hash: {last_news_hash}')

        time.sleep(1)


if __name__ == '__main__':
    main('news.csv')
