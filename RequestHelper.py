"""
Created on Apr 21, 2022

@author: arno

Request URL Helper to get response from API 
"""
import ssl
import time
from typing import Callable

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class RequestHelper():
    """
    Functions to help requesting response from an API
    """

    def __init__(self):
        self.session = self._init_session()
        self.view_update_waiting_time: Callable[[int], None]

    @staticmethod
    def _init_session():
        """Initialization of the session 
        """
        session = requests.Session()
        #session.headers.update({'Accept': 'application/json'})
        retry = Retry(total=5, backoff_factor=1.5,
                      respect_retry_after_header=False,  # False: show sleep time via this class
                      status_forcelist=[502, 503, 504])
        adapter = HTTPAdapter(max_retries=retry)
        session.mount('http://', adapter)
        session.mount('https://', adapter)
        return session

    def update_header(self, params: dict):
        """Update the header of the session 

        params = dictionary with parameters for the header
        """
        self.session.headers.update(params)

    def get_request_response(self, url: str, stream=False) -> dict:
        """general request url function 

        url = api url for request
        """
        resp = {}
        response = requests.Response
        request_timeout = 60
        verify = True
        requests.packages.urllib3.disable_warnings()  # type: ignore

        while True:
            try:
                response = self.session.get(
                    url, timeout=request_timeout, stream=stream, verify=verify)
                if response.status_code == 429:
                    if 'Retry-After' in response.headers.keys():
                        sleep_time = int(response.headers['Retry-After'])+1
                        self.sleep_print_time(sleep_time)
                    else:
                        break  # raise requests.exceptions.RequestException
                else:
                    break
            except requests.exceptions.SSLError as e:
                print('-1-Start-----------------------------------')
                print('Requests SSL Error:', e)
                verify = False  # raise
                # todo: Download ssl certification and try again
                # serverHost = 'proton.alcor.exchange'
                # serverPort = '443'
                # serverAddress = (serverHost, serverPort)
                # cert = ssl.get_server_certificate(serverAddress)
            except ssl.SSLCertVerificationError as e:
                print('-2-Start-----------------------------------')
                print('SSL Certification Error:', e)
                verify = False  # raise
            except requests.exceptions.RequestException as e:
                print('-3-Start-----------------------------------')
                print('Request exception:', e)
                # raise
            except Exception as e:
                print('-4-Start-----------------------------------')
                print('Exception:', e)
                # raise
            print('---End-------------------------------------')

        try:
            # get json from response, with type dict (mostly) or type list (Alcor exchange)
            resp_unknown = response.json()

            # when return type is a list, convert to dict
            if isinstance(resp_unknown, list):
                resp.update({'result': resp_unknown})
            else:
                resp = resp_unknown

        except Exception as e:
            print('JSON Exception: ', e)

        try:
            response.raise_for_status()
            resp.update({'status_code': response.status_code})

        except requests.exceptions.HTTPError as e:
            print('No status Exception: ', e)

            # check if error key is in result dictionary
            if 'error' in resp:
                resp.update({'status_code': 'error'})
            else:
                resp.update({'status_code': 'no status'})

        except Exception as e:
            print('Other Exception: ', e)  # , response.json())
            # raise
            resp.update({'status_code': 'error'})
            resp.update({'prices': []})

        return resp

    def api_url_params(self, url: str, params: dict, api_url_has_params=False):
        """
        Add params to the url

        url = url to be extended with parameters
        params = dictionary of parameters
        api_url_has_params = bool to extend url with '?' or '&'
        """
        if params:
            # if api_url contains already params and there is already a '?' avoid
            # adding second '?' (api_url += '&' if '?' in api_url else '?'); causes
            # issues with request parametes (usually for endpoints with required
            # arguments passed as parameters)
            url += '&' if api_url_has_params else '?'
            for key, value in params.items():
                if type(value) == bool:
                    value = str(value).lower()

                url += f'{key}={value}&'
            url = url[:-1]
        return url

    def sleep_print_time(self, sleeping_time: int):
        """
        Sleep and print countdown timer
        Used for a 429 response retry-after

        sleeping_time = total time to sleep in seconds
        """
        for i in range(sleeping_time, 0, -1):
            self.view_update_waiting_time(i)
            time.sleep(1)

    def attach_view_update_waiting_time(self, fn_waiting_time: Callable[[int], None]) -> None:
        """Set the viewers waiting time function to the coinprice program
        """
        self.view_update_waiting_time = fn_waiting_time


def __main__():
    pass


if __name__ == '__main__':
    __main__()
