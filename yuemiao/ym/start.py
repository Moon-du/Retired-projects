import threading
import time

from core.listening import Listening


def main():
    """生成线程开始监听"""
    process_pool = []
    # jnsj = threading.Thread(target=Listening("济南", "四价").start_listening)
    # process_pool.append(jnsj)
    jnjj = threading.Thread(target=Listening("济南", "九价").start_listening)
    process_pool.append(jnjj)
    # qdsj = threading.Thread(target=Listening("青岛", "四价").start_listening)
    # process_pool.append(qdsj)
    # qdjj = threading.Thread(target=Listening("青岛", "九价").start_listening)
    # process_pool.append(qdjj)
    for process in process_pool:
        process.start()
        time.sleep(2)


if __name__ == '__main__':
    main()
