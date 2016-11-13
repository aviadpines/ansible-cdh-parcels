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
                api_version = dict(default = 10),
                user = dict(default = None),
                password = dict(default = None),
                repos = dict(type = 'list', required = True)
                ),
            )

    if not HAS_CM_CLIENT:
        module.fail_json(msg='cm-api required for this module')

    host = module.params['host']
    api_version = module.params['api_version']
    user = module.params['user']
    password = module.params['password']
    repos = module.params['repos']

    api = cm_api(host, api_version, user, password)
    repositories = add_repos(api, repos)

    result = dict(
            results=dict(
                repositories = repositories,
            )
    )

    module.exit_json(**result)


if __name__ == '__main__':
    main()
