import json
import requests
from requests.auth import HTTPBasicAuth
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
import time
import uuid
import re
import os

auth = HTTPBasicAuth(os.environ.get('PC_USERNAME'),os.environ.get('PC_PASSWORD'))
PC_IP = "spe-pc.nxlab.fr"


def get_request(url, params):
    headers = {'Content-type': 'application/json','Accept': 'application/json'}
    resp=requests.get(url, params=params, auth=auth, headers=headers, verify=False)
    if resp.status_code == 200:
        return json.loads(resp.content)

def post_request(url, payload):
    headers = {'Content-type': 'application/json','Accept': 'application/json'}
    resp=requests.post(url, auth=auth, headers=headers, data=json.dumps(payload), verify=False)
    if resp.status_code == 200:
        return json.loads(resp.content)

#Post to calm api
def launch_mpi(bp_spec):
    headers = {'Content-type': 'application/json','Accept': 'application/json'}
    url1 = 'https://' + PC_IP + ':9440/api/nutanix/v3/blueprints/marketplace_launch'
    resp=requests.post(url1, auth=auth, headers=headers, data=json.dumps(bp_spec), verify=False)
    #print resp.content
    return json.loads(resp.content)

def convert_mpi_into_blueprint(mpi_name, mpi_version, project_name):
    bp_spec = {}
    project_uuid = get_project_uuid(project_name)
    project = get_project_by_uuid(project_uuid)
    env_uuid = get_environments_from_project(project_uuid)[0]["uuid"]

    data = get_mpi_by_name_n_version(mpi_name, mpi_version)
    NAME_RE = re.compile("[.|\s]+")
    bp_spec['spec'] = data['spec']['resources']['app_blueprint_template']['spec']
    del bp_spec['spec']['name']
    bp_spec['spec']['environment_uuid'] = env_uuid
    #Generate bp name as per user logic
    bp_name = "mpi_%s_%s" % (mpi_name.replace(".|\s", "_"), str(uuid.uuid4())[-7:])
    bp_spec['spec']['app_blueprint_name'] = "mpi_%s_%s" % (re.sub(NAME_RE,"_",mpi_name), str(uuid.uuid4())[-7:])
    bp_spec['metadata'] = {
        "kind": "blueprint",
        "project_reference": {
            "kind": "project",
            "uuid": project_uuid
        },
        "categories": data["metadata"].get("categories", {})
    }
    bp_spec['api_version'] = "3.0"

    response = launch_mpi(bp_spec)
    time.sleep(5)
    del response["spec"]["environment_uuid"]
    return response, bp_spec['metadata']



def list_mpi(filters):
    url = 'https://' + PC_IP + ':9440/api/nutanix/v3/marketplace_items/list'
    params = {"length": 250, 'filter': filters}
    return post_request(url=url, payload = params)

def get_mpi_app(app_uuid):
    """
    Appstore get REST API helper
    Args:
        app_uuid (str) : UUID to GET
    Returns:
        response (dict)
    """
    url = "https://" + PC_IP + ":9440/api/nutanix/v3/calm_marketplace_items/{}".format(app_uuid)
    return get_request(url=url, params={})

def get_mpi_by_name_n_version( mpi_name, mpi_version):
    """
    It will fetch marketplace item with particular version.
    Args:
        rest (object): Rest object
    Returns:
        apps (dict): All bp:uuid dict
    """
    filters = f"name=={mpi_name};version=={mpi_version}"

    response = list_mpi(filters)
    app_uuid = response['entities'][0]['metadata']['uuid']
    return get_mpi_app(app_uuid=app_uuid)

def get_project_uuid(project_name):
    for i in list_projects()['entities']:
        if i['spec']['name'] == project_name :
            return i['metadata']['uuid']
    return None

def list_projects():
    url = 'https://' + PC_IP + ':9440/api/nutanix/v3/projects/list'
    return post_request( url=url, payload={"length": 250} )

def get_project_by_uuid(project_uuid):
    url = 'https://' + PC_IP + ':9440/api/nutanix/v3/projects/{}'.format(project_uuid)
    return get_request( url=url, params={} )

def get_environments_from_project(project_uuid):
    response = get_project_by_uuid(project_uuid)
    return response["status"]['resources']["environment_reference_list"]


def deploy_app(bp_spec, bp_uuid, appname, timeout=1200):
    payload = bp_spec
    del payload['spec']['name']
    del payload['status']
    payload['spec']['application_name'] = appname
    payload['spec']['app_profile_reference'] = {'kind': 'app_profile', 'uuid':payload['spec']['resources']['app_profile_list'][0]['uuid']}

    #profile value to be modified here
    payload['spec']['resources']['app_profile_list'][0]['variable_list'][0]['value']="new_value_option1"
    payload['spec']['resources']['app_profile_list'][0]['variable_list'][1]['value']="new_value_option2"
    

    #Post to calm api
    url1 = "https://" + PC_IP + ":9440/api/nutanix/v3/blueprints/"+bp_uuid+"/launch"
    headers = {'Content-type': 'application/json','Accept': 'application/json'}
    resp=requests.post(url1, auth=auth, headers=headers, data=json.dumps(payload), verify=False)
    return resp

def launch(mpname, mpversion, projectname, appname):

    headers = {'Content-type': 'application/json', 'Accept': 'application/json'}
    bp_response, metadata = convert_mpi_into_blueprint(mpname, mpversion, projectname)
    blueprint_status = bp_response['status']['state']
    bp_uuid = bp_response['metadata']['uuid']
    if blueprint_status == "ACTIVE":
        resp = deploy_app(bp_response, bp_uuid, appname)
    payload=resp.json()
    request_id=payload['status']['request_id']

    #Get launch status
    url1="https://" + PC_IP + ":9440/api/nutanix/v3/blueprints/"+bp_uuid+"/pending_launches/"+str(request_id)
    while True:
        resp=requests.get(url1, auth=auth, headers=headers, verify=False)
        payload=resp.json()
        launch_state=payload['status']['state']
        if launch_state == 'success':
            print("App request is successfull")
            app_uuid=payload['status']['application_uuid']
            break
        elif launch_state == 'failed':
            print("App request failed")
            sys.exit(1)
            break
        print("App request is in pending state")
        time.sleep(10)

    url1="https://" + PC_IP + ":9440/api/nutanix/v3/apps/"+str(app_uuid)
    while True:
        resp=requests.get(url1, auth=auth, headers=headers, verify=False)
        payload=resp.json()
        app_state=payload['status']['state']
        if app_state == 'running':
            print("App is launched successfull")
            break
        elif app_state == 'error' or app_state == 'failed':
            print("App launch failed")
            sys.exit(1)
            break
        print("App is in provisioning state")
        time.sleep(10)