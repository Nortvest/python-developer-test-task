# Парсер биржи криптовалют ByBit.
### Каждую секунду проверяет наличие новых новостей на сайте. При нахождении написывает в файл.

В файле main.py находится 1 класс (ByBitParser) и 3 функции (filter_news, save_to_csv и main)<br>
  • __ByBitParser__ - класс парсера. При каждом вызове метода start возвращает новости с первой страницы.<br>
  • __filter_news__ - функция фильтрации новостей. На вход подаются новости из метода start класса ByBitParser, на выходе остаются только свежие новости.<br>
  • __save_to_csv__ - функция, сохраняющая новости в файл.<br>
  • __main__ - основная функция. В ней вызываются все остальные функции и методы.
