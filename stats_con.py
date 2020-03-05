import requests
import json
import datetime
import keyring
import base64
import logging

log=logging.getLogger()
class Fitbit():
    def __init__(self):
        self.storage='creds_fitbit.txt'
        try:
            with open(self.storage,'r') as f:
                datastore=json.load(f)
        except IOError:
            log.critical("Credentials do not exist, need to creade creds.txt")
            exit()
        # Probably should be here, at least use keyring instead
        self._client_id=keyring.get_password('Fitbit','client_id')
        self._client_secret=keyring.get_password('Fitbit','client_secret')
        self.access_token=datastore['access_token']
        self.expires_in=datastore['expires_in']
        self.refresh_token=datastore['refresh_token']
        self.user_id=datastore['user_id']
        self.client_encoded=base64.b64encode((self._client_id+':'+self._client_secret).encode("utf-8")).decode("utf-8")
        self.validate_initial_token()
        self.set_access_token()

    def set_access_token(self):
        if self.valid_token():
            self.access_token=self.access_token
        else:
            token_str=self.refresh()
            token_json=token_str.json()
            log.info('New Credentials Issued')
            self.store_creds(token_json)
            try:
                self.access_token=token_json['access_token']
                self.expires_in=token_json['expires_in']
            except:
                log.critical("Could not set new token values")
                exit()

    def validate_initial_token(self):
        base_url='https://api.fitbit.com/1.1/oauth2/introspect'
        api_call_headers = {'Authorization': 'Bearer ' + self.access_token}
        data={'token':self.access_token}

        r=requests.post(base_url,headers=api_call_headers,data=data)
        if r.status_code==200:
            check=r.json()
            if check['active']:
                self.expires_at=check['exp']
            else:
                self.expires_at=0
        elif r.status_code==401:
            log.warning('Current token unauthorized')
            check=r.json()
            try:
                type=check['errors'][0]['errorType']
                if type=='expired_token':
                    log.info('Token Expired')
                    self.expires_at=0
                else:
                    log.critical('Error with token check '+str(type))
            except:
                log.critical('No Response, is connection working')
        else:
            log.critical('Something went wrong')

    def valid_token(self):
        if self.expires_at>=datetime.datetime.utcnow().timestamp():
            return True
        else:
            return False

    def refresh(self):
        log.info('Trying to Refresh Fitbit Token')
        refresh_base_url="https://api.fitbit.com/oauth2/token"
        auth_header={"Authorization":"Basic "+self.client_encoded}
        data={'grant_type':'refresh_token','refresh_token':self.refresh_token, 'expires_in':28800}
        r=requests.post(refresh_base_url, headers=auth_header, data=data)
        if r.status_code==200:
            self.expires_in=r.json()['expires_in']
            #print(self.expires_in)
            self.expires_at=datetime.datetime.utcnow().timestamp()+int(self.expires_in)
            return r
        else:
            log.critical('Could not refresh token')
            exit()

    def store_creds(self,r):
        if len(r) > 0:
            try:
                with open(self.storage,'w') as outfile:
                    json.dump(r,outfile)
            except:
                log.warning("Issue with credential storage")
        else:
            log.warning("No Response for Storage")

    def get_weight(self, date=datetime.datetime.now().strftime('%Y-%m-%d'),period='30d'):
        api_call_headers = {'Authorization': 'Bearer ' + self.access_token,
        'Accept-Language':'en_US'}
        base_url='https://api.fitbit.com/1/user/'+self.user_id
        endpoint='/body/log/weight/date/'+date+'/'+period+'.json'

        try:
            if self.valid_token():
                r=requests.get(base_url+endpoint, headers=api_call_headers)
            else:
                self.refresh()
                r=requests.get(base_url+endpoint, headers=api_call_headers)
            if r.status_code==200:
                return r
            else:
                log.warning('Could not get Weight')
                return r
        except:
            log.critical('Something went wrong')
            return 'API Problem'

    def get_calories(self, date=datetime.datetime.now().strftime('%Y-%m-%d'),period='30d'):
        api_call_headers = {'Authorization': 'Bearer ' + self.access_token,
        'Accept-Language':'en_US'}
        base_url='https://api.fitbit.com/1/user/'+self.user_id
        endpoint='/foods/log/caloriesIn/date/'+date+'/'+period+'.json'

        try:
            if self.valid_token():
                r=requests.get(base_url+endpoint, headers=api_call_headers)
            else:
                self.refresh()
                r=requests.get(base_url+endpoint, headers=api_call_headers)
            if r.status_code==200:
                return r
            else:
                log.warning('Could not get Weight')
                return r
        except:
            log.critical('Something went wrong')
            return 'API Problem'

if __name__=="__main__":
    fbit=Fitbit()
    print(fbit.access_token)
    print(json.dumps(fbit.get_weight().json(), indent=4, sort_keys=True))
    print(json.dumps(fbit.get_calories().json(), indent=4, sort_keys=True))

class Strava():
    def __init__(self):
        self.storage='creds.txt'
        try:
            with open(self.storage,'r') as f:
                datastore=json.load(f)
        except IOError:
            log.warning("Credentials do not exist, need to creade creds.txt")
            exit()
        # Probably should be here, at least use keyring instead
        self._client_id=keyring.get_password('Strava','client_id')#'43801'
        self._client_secret=keyring.get_password('Strava','client_secret')#51cfd621f26e736c47193e9b4cece0d0d216db37'
        self.access_token=datastore['access_token']
        self.expires_at=datastore['expires_at']
        self.expires_in=datastore['expires_in']
        self.refresh_token=datastore['refresh_token']

        self.set_access_token()

    def set_access_token(self):
        if self.valid_token():
            self.access_token=self.access_token
        else:
            token_str=self.refresh()
            token_json=token_str.json()
            log.info('New Credentials Obtained',token_json)
            self.store_creds(token_json)
            try:
                self.access_token=token_json['access_token']
                self.expires_in=token_json['expires_in']
            except:
                log.warning("Could not set new token values")
                exit()

    def valid_token(self):
        if self.expires_at>=datetime.datetime.utcnow().timestamp():
            return True
        else:
            return False

    def refresh(self):
        log.info('Trying to Refresh Token')
        refresh_base_url="https://www.strava.com/api/v3/oauth/token"
        refresh_url=refresh_base_url+\
        '?client_id='+self._client_id+\
        '&client_secret='+self._client_secret+\
        '&grant_type=refresh_token'+\
        '&refresh_token='+self.refresh_token
        r=requests.post(refresh_url)
        if r.status_code==200:
            return r
        else:
            log.critical('Could not refresh token')
            exit()

    def store_creds(self,r):
        print('JSON',r)
        if len(r) > 0:
            try:
                with open(self.storage,'w') as outfile:
                    json.dump(r,outfile)
            except:
                log.warning("Issue with credentials")
        else:
            log.warning("No Response to Token Storage")

    def get_activities(self, before='',after='',page=1,per_page=30):
        api_call_headers = {'Authorization': 'Bearer ' + self.access_token}
        activities_url="https://www.strava.com/api/v3/athlete/activities?"
        try:
            if self.valid_token():
                r=requests.get(activities_url, headers=api_call_headers, verify=False)
            else:
                self.refresh()
                r=requests.get(activities_url, headers=api_call_headers, verify=False)
            if r.status_code==200:
                log.info('Activities obtained')
                return r
            else:
                log.warning('Could not get activities')
                return r
            return r
        except:
            log.critical('Something went wrong')
            return('API Problem')

if __name__=="__main__":
    strv=Strava()
    print(strv.access_token)
    print(json.dumps(strv.get_activities().json(), indent=4, sort_keys=True))
