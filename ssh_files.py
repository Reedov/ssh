"""
    работа с ssh и sftp
"""
import configparser
from paramiko import SSHClient, AutoAddPolicy, Transport, SFTPClient  # pip install paramiko
from os import path
import logging
logging.basicConfig(format='%(asctime)s - %(levelname)s [%(funcName)s:%(lineno)s] %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

SETTINGS_FILE = 'settings.ini'

config = configparser.ConfigParser()
config.read(SETTINGS_FILE)
default = config['DEFAULT']

HOST = default['HOST']
SFTP_PORT = int(default['SFTP_PORT'])
USERNAME = default['USERNAME']
PASSWORD = default['PASSWORD']
REMOTE_PATH = default['REMOTE_PATH']
REMOTE_FILEXTENTION = default['REMOTE_FILEXTENTION']
LOCAL_PATH = default.get('LOCAL_PATH', '')


class SSH:
    """ класс работы с ssh """
    def __init__(self, host=HOST, username=USERNAME, password=PASSWORD):
        self.client = SSHClient()
        self.client.set_missing_host_key_policy(AutoAddPolicy())
        self.client.connect(host, username=username, password=password)

    def get_file_list(self, remote_path: str, file_extention: str) -> list:
        """ получить список файлов по маске """
        stdin, stdout, stderr = self.client.exec_command(f'ls {remote_path}*{file_extention}')
        return stdout.readlines()

    def delete_file(self, filepath: str) -> tuple:
        """ удалить файл """
        stdin, stdout, stderr = self.client.exec_command(f'rm {filepath}')
        return stdout.readlines(), stderr.readlines()


class SFTP:
    """ класс работы с sftp """
    def __init__(self, host=HOST, port=SFTP_PORT, username=USERNAME, password=PASSWORD):
        self.transport = Transport(host, port)
        self.transport.connect(username=username, password=password)
        self.sftp = SFTPClient.from_transport(self.transport)

    def get_file(self, remote_filepath: path, local_filepath: path):
        """ скачать файл с сервера """
        self.sftp.get(remotepath=remote_filepath, localpath=local_filepath)

    def put_file(self, local_filepath: str, remote_filepath: str):
        """ закачать файл на сервер """
        self.sftp.put(localpath=local_filepath, remotepath=remote_filepath)


def main():
    """ Получить список файлов с расширением REMOTE_FILEXTENTION в директории REMOTE_PATH
        скачать файлы в локальную директорию LOCAL_PATH,
        удалить эти файлы на сервере.
    """
    ssh = SSH()
    files = ssh.get_file_list(REMOTE_PATH, REMOTE_FILEXTENTION)
    if not files:
        logger.info(f'there is no files *{REMOTE_FILEXTENTION} at {HOST}{REMOTE_PATH}')
        return

    sftp_client = SFTP()
    for file in files:
        filepath = file.strip()
        filename = path.basename(filepath)
        local_filepath = path.join(LOCAL_PATH, filename)
        sftp_client.get_file(remote_filepath=filepath, local_filepath=local_filepath)
        is_local_file_exists = True if path.isfile(local_filepath) else False
        if is_local_file_exists:
            success, failure = ssh.delete_file(filepath)
            if failure:
                logger.error(f'cant remove {filepath}, error: {failure}')
            else:
                logger.info(f'{filepath} is deleted')


if __name__ == "__main__":
    main()
