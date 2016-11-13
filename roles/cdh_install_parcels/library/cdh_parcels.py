#!/usr/bin/python

def cm_api(cm_host, cm_api_version, cm_user, cm_pass):
    return ApiResource(cm_host, version=cm_api_version, username=cm_user, password=cm_pass)


def download_parcel(cluster, parcel, timeout):
    try:
        pd = parcel.start_download()
        if pd.success != True:
            return "FAILED: Could not start downloading parcel"
        curr_timeout = 0
        while parcel.stage != 'DOWNLOADED' and curr_timeout < timeout:
            parcel = cluster.get_parcel(parcel.product, parcel.version)
            if parcel.state.errors:
                return "FAILED: " + str(parcel.state.errors) + '.'
            time.sleep(15)
            curr_timeout += 15
        if parcel.stage == 'DOWNLOADED':
            return "OK"
        return "FAILED: Timed out (Perhaps the parcel is already downloaded and distributed?)"
    except Exception as e:
        return "FAILED: %s" % (e)


def distribute_parcel(cluster, parcel, timeout):
    try:
        pd = parcel.start_distribution()
        if pd.success != True:
            return "FAILED: Could not start distributing parcel"
        curr_timeout = 0
        while parcel.stage != 'DISTRIBUTED' and curr_timeout < timeout:
            parcel = cluster.get_parcel(parcel.product, parcel.version)
            if parcel.state.errors:
                return "FAILED: " + str(parcel.state.errors) + '.'
            time.sleep(15)
            curr_timeout += 15
        if parcel.stage == 'DISTRIBUTED':
            return "OK"
        return "FAILED: Timed out (Perhaps the parcel is already downloaded and distributed?)"
    except Exception as e:
        return "FAILED: %s" % (e)


def activate_parcel(cluster, parcel, timeout):
    try:
        pd = parcel.activate()
        if pd.success != True:
            return "FAILED: Could not activate parcel"
        curr_timeout = 0
        while parcel.stage != 'ACTIVATED' and curr_timeout < timeout:
            parcel = cluster.get_parcel(parcel.product, parcel.version)
            if parcel.state.errors:
                return "FAILED: " + str(parcel.state.errors) + '.'
            time.sleep(15)
            curr_timeout += 15
        if parcel.stage == 'ACTIVATED':
            return "OK"
        return "FAILED: Timed out"
    except Exception as e:
        return "FAILED: %s" % (e)


def handle_parcels(api, parcels, action_func, timeout):
    results = dict()
    for cluster in api.get_all_clusters():
        results[cluster.name] = dict()
        for service, version in parcels.iteritems():
            parcel = cluster.get_parcel(service, version)
            results[cluster.name][service] = dict()
            results[cluster.name][service][version] = dict()
            results[cluster.name][service][version] = action_func(cluster, parcel, timeout)
    return results





import time
from ansible.module_utils.basic import AnsibleModule

try:
    from cm_api.api_client import ApiResource
    HAS_CM_CLIENT = True
except ImportError:
    HAS_CM_CLIENT = False

def main():
    module = AnsibleModule(
            argument_spec = dict(
                host = dict(required = True),
                api_version = dict(default = 1),
                user = dict(default = None),
                password = dict(default = None),
                parcels = dict(type = 'dict', required = True),
                action = dict(type = 'str', choices = ['download', 'distribute', 'activate'], default = []),
                timeout = dict(type = 'int', default = 180)
                ),
            )

    if not HAS_CM_CLIENT:
        module.fail_json(msg='cm-api required for this module')

    host = module.params['host']
    api_version = module.params['api_version']
    user = module.params['user']
    password = module.params['password']
    parcels = module.params['parcels']
    action = module.params['action']
    timeout = module.params['timeout']

    api = cm_api(host, api_version, user, password)

    func = {
        'download': download_parcel,
        'distribute': distribute_parcel,
        'activate': activate_parcel
    }[action]

    parcels = handle_parcels(api, parcels, func, timeout)

    result = dict(
            results=dict(
                parcels = parcels
            )
    )

    module.exit_json(**result)


if __name__ == '__main__':
    main()
