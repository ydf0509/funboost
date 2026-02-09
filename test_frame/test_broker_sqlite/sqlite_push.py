

from sqlite_consume import process_message


if __name__ == '__main__':
    for i in range(100000):
        process_message.push(i, i * 2)