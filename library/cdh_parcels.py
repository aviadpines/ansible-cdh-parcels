#!/usr/bin/python

def cm_api(cm_host, cm_api_version, cm_user, cm_pass):
    return ApiResource(cm_host, version=cm_api_version, username=cm_user, password=cm_pass)


def add_repos(api, repos):
    cm_config = api.get_cloudera_manager().get_config(view='full')
    repo_config = cm_config['REMOTE_PARCEL_REPO_URLS']
    existing_repos = (repo_config.value or repo_config.default).split(',')
    added_repos = []
    for repo in repos:
        if repo not in existing_repos:
            added_repos += [repo]
    api.get_cloudera_manager().update_config({'REMOTE_PARCEL_REPO_URLS': ','.join(existing_repos + added_repos)})
    time.sleep(10)
    return dict(pre_existing_repos = existing_repos, added_repos = added_repos)


def download_parcel(cluster, parcel):
    try:
        pd = parcel.start_download()
        if pd.success != True:
            result = "FAILED: Could not start downloading parcel"
        while parcel.stage != 'DOWNLOADED':
            parcel = cluster.get_parcel(parcel.product, parcel.version)
            if parcel.state.errors:
                return "FAILED: " + str(parcel.state.errors) + '.'
            time.sleep(15)
        if parcel.stage == 'DOWNLOADED':
            return "OK" 
    except Exception as e:
        return "FAILED: %s" % (e)   


def distribute_parcel(cluster, parcel):
    try:
        pd = parcel.start_distribution()
        if pd.success != True:
            result = "FAILED: Could not start distributing parcel"
        while parcel.stage != 'DISTRIBUTED':
            parcel = cluster.get_parcel(parcel.product, parcel.version)
            if parcel.state.errors:
                return "FAILED: " + str(parcel.state.errors) + '.'
            time.sleep(15)
        if parcel.stage == 'DISTRIBUTED':
            return "OK" 
    except Exception as e:
        return "FAILED: %s" % (e)   

def activat_parcel(cluster, parcel):
    try:
        pd = parcel.activate()
        if pd.success != True:
            result = "FAILED: Could not activate parcel"
        while parcel.stage != 'ACTIVATED':
            parcel = cluster.get_parcel(parcel.product, parcel.version)
            if parcel.state.errors:
                return "FAILED: " + str(parcel.state.errors) + '.'
            time.sleep(15)
        if parcel.stage == 'ACTIVATED':
            return "OK" 
    except Exception as e:
        return "FAILED: %s" % (e)   



def handle_parcels(api, parcels):
    results = dict()
    for cluster in api.get_all_clusters():
        results[cluster.name] = dict()
        for service, version in parcels.iteritems():
            parcel = cluster.get_parcel(service, version)
            results[cluster.name][service] = dict()
            results[cluster.name][service][version] = dict()
            results[cluster.name][service][version]['download'] = download_parcel(cluster, parcel)
            results[cluster.name][service][version]['distribute'] = distribute_parcel(cluster, parcel)
            results[cluster.name][service][version]['activate'] = activate_parcel(cluster, parcel)
    return results


import time
from cm_api.api_client import ApiResource
from ansible.module_utils.basic import AnsibleModule

def main():
    module = AnsibleModule(
            argument_spec = dict(
                host = dict(required = True),
                api_version = dict(default = 10),
                user = dict(default = None),
                password = dict(default = None),
                parcels = dict(type = 'dict', required = True),
                repos = dict(type = 'list', default = [])
                ),
            )

    host = module.params['host']
    api_version = module.params['api_version']
    user = module.params['user']
    password = module.params['password']
    parcels = module.params['parcels']
    repos = module.params['repos']

    api = cm_api(host, api_version, user, password)
    repositories = add_repos(api, repos)
    downloaded_parcels = handle_parcels(api, parcels)
    result = dict(
            results=dict(
                repositories = repositories,
                parcels = downloaded_parcels
            )
    )

    module.exit_json(**result)


if __name__ == '__main__':
    main()
