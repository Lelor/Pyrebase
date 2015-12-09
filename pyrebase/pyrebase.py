from operator import itemgetter
import requests
from firebase_token_generator import create_token
from urllib.parse import urlencode, quote
import re
import json


class Firebase():
    """ Firebase Interface """
    def __init__(self, fire_base_url, fire_base_secret):
        if not fire_base_url.endswith('/'):
            url = ''.join([fire_base_url, '/'])
        else:
            url = fire_base_url

        # find db name between http:// and .firebaseio.com
        db_name = re.search('https://(.*).firebaseio.com', fire_base_url)
        if db_name:
            name = db_name.group(1)
        else:
            db_name = re.search('(.*).firebaseio.com', fire_base_url)
            name = db_name.group(1)

        self.requests = requests.Session()
        self.fire_base_url = url
        self.fire_base_name = name
        self.secret = fire_base_secret
        self.token = None
        self.uid = None
        self.email = None
        self.password = None
        self.path = ""
        self.buildQuery = {}

    def admin(self):
        auth_payload = {"uid": "1"}
        options = {"admin": True}
        token = create_token(self.secret, auth_payload, options)
        self.token = token
        return self

    def user(self, email, password):
        request_ref = 'https://auth.firebase.com/auth/firebase?firebase={0}&email={1}&password={2}'.\
            format(self.fire_base_name, email, password)
        request_object = self.requests.get(request_ref)
        request_json = request_object.json()
        self.uid = request_json['user']['uid']
        self.token = request_json['token']
        self.email = email
        self.password = password
        return self

    def create_user(self, email, password):
        request_ref = 'https://auth.firebase.com/auth/firebase/create?firebase={0}&email={1}&password={2}'.\
            format(self.fire_base_name, email, password)
        request_object = self.requests.get(request_ref)
        request_json = request_object.json()
        return request_json

    def remove_user(self, email, password):
        request_ref = 'https://auth.firebase.com/auth/firebase/remove?firebase={0}&email={1}&password={2}'.\
            format(self.fire_base_name, email, password)
        request_object = self.requests.get(request_ref)
        request_json = request_object.json()
        return request_json

    def change_password(self, email, new_password):
        request_ref = 'https://auth.firebase.com/auth/firebase/update?firebase={0}&email={1}&newPassword={2}'.\
            format(self.fire_base_name, email, new_password)
        request_object = self.requests.get(request_ref)
        request_json = request_object.json()
        return request_json

    def send_password_reset_email(self, email, new_password):
        request_ref = 'https://auth.firebase.com/auth/firebase/reset_password?firebase={0}&email={1}'.\
            format(self.fire_base_name, email, new_password)
        request_object = self.requests.get(request_ref)
        request_json = request_object.json()
        return request_json

    def orderBy(self, order):
        self.buildQuery["orderBy"] = order
        return self

    def startAt(self, start):
        self.buildQuery["startAt"] = start
        return self

    def endAt(self, end):
        self.buildQuery["endAt"] = end
        return self

    def equalTo(self, equal):
        self.buildQuery["equalTo"] = equal
        return self

    def limitToFirst(self, limitFirst):
        self.buildQuery["limitToLast"] = limitFirst
        return self

    def limitToLast(self, limitLast):
        self.buildQuery["limitToLast"] = limitLast
        return self

    def shallow(self):
        self.buildQuery["shallow"] = True
        return self

    def child(self, *args):
        new_path = "/".join(args)
        if self.path:
            self.path += "/{}".format(new_path)
        else:
            if new_path.startswith("/"):
                new_path = new_path[1:]
            self.path = new_path
        return self

    def get(self):
        parameters = {}
        parameters['auth'] = self.token
        for param in list(self.buildQuery):
            if type(self.buildQuery[param]) is str:
                parameters[param] = quote('"' + self.buildQuery[param] + '"')
            else:
                parameters[param] = self.buildQuery[param]
        request_ref = '{0}{1}.json?{2}'.format(self.fire_base_url, self.path, urlencode(parameters))
        # reset path and buildQuery for next query
        self.path = ""
        buildQuery = self.buildQuery
        self.buildQuery = {}
        # do request
        request_object = self.requests.get(request_ref)
        # return if error
        if request_object.status_code != 200:
            return {"error": request_object.text, "status_code": request_object.status_code}
        request_dict = request_object.json()
        # if primitive or simple query return
        if not isinstance(request_dict, dict) or not buildQuery:
            return request_dict
        # return keys if shallow is enabled
        if buildQuery.get("shallow"):
            return request_dict.keys()
        # otherwise sort
        if buildQuery.get("orderBy"):
            if buildQuery["orderBy"] in ["$key", "key"]:
                return sorted(list(request_dict))
            else:
                return sorted(request_dict.values(), key=itemgetter(buildQuery["orderBy"]))

    def info(self):
        info_list = {'url': self.fire_base_url, 'token': self.token, 'email': self.email, 'password': self.password,
                     'uid': self.uid}
        return info_list

    def push(self, data):
        request_ref = '{0}{1}.json?auth={2}'.format(self.fire_base_url, self.path, self.token)
        self.path = ""
        request_object = self.requests.post(request_ref, data=dump(data))
        return request_object.status_code

    def set(self, data):
        request_ref = '{0}{1}.json?auth={2}'.format(self.fire_base_url, self.path, self.token)
        self.path = ""
        request_object = self.requests.put(request_ref, data=dump(data))
        return request_object.status_code

    def update(self, data):
        request_ref = '{0}{1}.json?auth={2}'.format(self.fire_base_url, self.path, self.token)
        self.path = ""
        request_object = self.requests.patch(request_ref, data=dump(data))
        return request_object.status_code

    def remove(self):
        request_ref = '{0}{1}.json?auth={2}'.format(self.fire_base_url, self.path, self.token)
        self.path = ""
        request_object = self.requests.delete(request_ref)
        return request_object.status_code


def dump(data):
    if isinstance(data, dict):
        return json.dumps(data)
    else:
        return data
