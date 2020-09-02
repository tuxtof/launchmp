from . import base
from .utils import launch
from flask import request, abort, jsonify

@base.route('/health')
def health():
    return jsonify({"status":"ready"})

@base.route('/')
def status():
    return jsonify({'result': 'ready'}), 200


@base.route('/api/v1/mplaunch', methods=['GET', 'POST'])
def launchmpx():
    if (not request.json) or \
            (not 'mpname' in request.json) or \
            (not 'mpversion' in request.json) or \
            (not 'appname' in request.json) or \
            (not 'projectname' in request.json):
        abort(400)
    mpname = request.json.get('mpname', 'N/A')
    mpversion = request.json.get('mpversion', "N/A")
    projectname = request.json.get('projectname', "N/A")
    appname = request.json.get('appname', "N/A")

    launch(mpname, mpversion, projectname, appname)

    return jsonify({'result': 'success'}), 201
