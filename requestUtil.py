import re
import traceback

import requests
import warnings

from urllib3 import encode_multipart_formdata
# import test65_nsa

warnings.filterwarnings("ignore")

headers = {
}

proxy = {
    "http": "http://127.0.0.1:8082",
    "https": "http://127.0.0.1:8082",
}

# cookies = "test65_nsa.cookies"
cookies = ""

def get_cookies(cookie_str):
    cookie_dict = {i.split("=")[0].strip(): "=".join(i.split("=")[1:]).strip() for i in cookie_str.split(";")}
    return cookie_dict


def get(url, cookies=cookies, header=None, timeout=50, session="", allow_redirects=True, stream=False, proxable=False):
    f_headers = dict.copy(headers)
    if cookies == "":
        cookies = {}
    else:
        cookies = get_cookies(cookies)
    if header == None:
        header = {}
    f_headers = dict(header, **f_headers)
    if proxable:
        proxies = proxy
    else:
        proxies = {}
    try:
        if session == "":
            resp = requests.get(url, verify=False, headers=f_headers, cookies=cookies, timeout=timeout,
                                allow_redirects=allow_redirects, stream=stream, proxies=proxies)
        else:
            resp = session.get(url, cookies=cookies, headers=f_headers, verify=False, timeout=timeout,
                               allow_redirects=allow_redirects, stream=stream, proxies=proxies)
        if resp != None and '<h1>Burp Suite Professional</h1>' in resp.text:
            raise Exception
        return resp
    except Exception as e:
        print(e)
        return None


def post(url, data="", cookies=cookies, header=None, timeout=5, session="", files=None, proxable=False, allow_redirects=True, changeHeader=True):
    f_headers = dict.copy(headers)
    if cookies == "":
        cookies = {}
    else:
        cookies = get_cookies(cookies)
    if header == None:
        header = {}
    if not "Content-Type" in header and not files and changeHeader:
        header = dict(header, **{"Content-Type": "application/x-www-form-urlencoded"})
    if files == None:
        files = {}
    f_headers = dict(header, **f_headers)
    if proxable:
        proxies = proxy
    else:
        proxies = {}
    try:
        if session == "":
            resp = requests.post(url, cookies=cookies, data=data, headers=f_headers, verify=False, timeout=timeout,
                                 files=files, proxies=proxies, allow_redirects=allow_redirects)
        else:
            resp = session.post(url, cookies=cookies, data=data, headers=f_headers, verify=False, timeout=timeout,
                                files=files, proxies=proxies, allow_redirects=allow_redirects)
        if resp != None and '<h1>Burp Suite Professional</h1>' in resp.text:
            print("aa")
            raise Exception
        return resp
    except Exception as e:
        return None
        # print(e)

def put(url):
    return requests.put(url, verify=False)

class FileData:
    def __init__(self, header, data):
        self.header = header
        self.data = data


def get_file_data(filename="", filedata="", param="file", data=None):  # param: 上传文件的POST参数名
    if not data:
        data = {}
    if filename:
        data[param] = (filename, filedata)  # 名称，文件内容
    encode_data = encode_multipart_formdata(data)
    file_data = FileData({"Content-Type": encode_data[1]}, encode_data[0])
    return file_data


def session():
    return requests.session()


def get_title(resp):
    try:
        try:
            content = resp.content.decode()
        except:
            content = resp.content.decode("GBK", "ignored")
        title = re.findall("<title>(.*?)</title>", content)[0]
    except:
        title = "[空标题]"
    return title


def get_ip(url):
    if re.findall("http://(.*?)/", url):
        return re.findall("http://(.*?)/", url)
    else:
        return re.findall("http://(.*)", url)

def print_info(resp):
    if resp != None:
        print (resp.url, resp.status_code, len(resp.text), get_title(resp))

