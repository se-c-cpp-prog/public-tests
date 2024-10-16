# Тесты к курсу «Основы программирования»

Условия лабораторных работ вы можете найти в таблице курса.

Порядок запуска локального тестирования:

1. Склонировать этот репозиторий
2. Скомпилировать разработанную программу
3. Проверить, что создался исполняемый файл (в Windows по умолчанию это `a.exe`, в Linux - `a.out`)
4. В каталоге, в котором находится этот файл, выполнить команду:

    ```bash
    python3 <путь к main.py> --program [a.exe|a.out|<другое название исполняемого файла>] --suite <выбор задания>
    ```

5. Для ускорения отладки рекомендуется сделать скрипт, выполняющий шаги 2-4.

## Лабораторные работы

Ниже представлена таблица доступных для тестирования (как локально, так и автоматически в репозиториях) лабораторных работ с названием набора тестов для тестера (`suite`).

| №  | Лабораторная работа | Набор тестов |
|:--:|:--------------------|:-------------|
| 0  | Сумма чисел         | `sum`        |

## Скрипт запуска

Тестер выполняет тестирование программы методом "чёрного ящика", то есть на вход *input* программа выдаёт какой-то выход *output*, который должен быть правильным с точки зрения текущего теста. Необходимыми и достаточными параметрами [`main.py`](main.py) являются:

* `--program` - путь к исполняемому файлу;
* `--suite` - выбор задания.

В случае, если хочется проверить программу только на правильность возвращаемых кодов возврата:

* `--check-output [True|False]` - включение/отключение проверки выходного значения порождённого процесса программы (по умолчанию - `True`).

Поскольку разные анализаторы и санитайзеры могут замедлить вашу программу (например, [Valgrind](https://valgrind.org/) с выбранным `memcheck` замедляет программу в 10-30 раз), то имеет смысл установить множитель максимального времени исполнения процесса на все тесты:

* `--timeout-factor <float>` - множитель максимального времени исполнения порождённого процесса программы (по умолчанию - `1.0`).
