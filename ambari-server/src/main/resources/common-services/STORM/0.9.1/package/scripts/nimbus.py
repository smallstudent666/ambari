#!/usr/bin/env python
"""
Licensed to the Apache Software Foundation (ASF) under one
or more contributor license agreements.  See the NOTICE file
distributed with this work for additional information
regarding copyright ownership.  The ASF licenses this file
to you under the Apache License, Version 2.0 (the
"License"); you may not use this file except in compliance
with the License.  You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

"""

import sys
from resource_management.libraries.functions import check_process_status
from resource_management.libraries.script import Script
from resource_management.libraries.functions import format
from resource_management.libraries.functions import conf_select
from resource_management.libraries.functions import stack_select
from resource_management.core.resources.system import Execute
from resource_management.libraries.functions.stack_features import check_stack_feature
from resource_management.libraries.functions import StackFeature
from storm import storm
from service import service
from resource_management.libraries.functions.security_commons import build_expectations, \
  cached_kinit_executor, get_params_from_filesystem, validate_security_config_properties, \
  FILE_TYPE_JAAS_CONF
from setup_ranger_storm import setup_ranger_storm
from ambari_commons import OSConst
from ambari_commons.os_family_impl import OsFamilyImpl
from resource_management.core.resources.service import Service

class Nimbus(Script):
  def get_component_name(self):
    return "storm-nimbus"

  def install(self, env):
    self.install_packages(env)
    self.configure(env)

  def configure(self, env):
    import params
    env.set_params(params)
    storm("nimbus")


@OsFamilyImpl(os_family=OsFamilyImpl.DEFAULT)
class NimbusDefault(Nimbus):

  def pre_upgrade_restart(self, env, upgrade_type=None):
    import params
    env.set_params(params)
    if params.version and check_stack_feature(StackFeature.ROLLING_UPGRADE, params.version):
      conf_select.select(params.stack_name, "storm", params.version)
      stack_select.select("storm-client", params.version)
      stack_select.select("storm-nimbus", params.version)


  def start(self, env, upgrade_type=None):
    import params
    env.set_params(params)
    self.configure(env)
    setup_ranger_storm(upgrade_type=upgrade_type)
    service("nimbus", action="start")

    if "SUPERVISOR" not in params.config['localComponents']:
      service("logviewer", action="start")


  def stop(self, env, upgrade_type=None):
    import params
    env.set_params(params)
    service("nimbus", action="stop")

    if "SUPERVISOR" not in params.config['localComponents']:
      service("logviewer", action="stop")


  def status(self, env):
    import status_params
    env.set_params(status_params)
    check_process_status(status_params.pid_nimbus)

  def get_log_folder(self):
    import params
    return params.log_dir

  def get_user(self):
    import params
    return params.storm_user

@OsFamilyImpl(os_family=OSConst.WINSRV_FAMILY)
class NimbusWindows(Nimbus):
  def start(self, env):
    import status_params
    env.set_params(status_params)
    Service(status_params.nimbus_win_service_name, action="start")

  def stop(self, env):
    import status_params
    env.set_params(status_params)
    Service(status_params.nimbus_win_service_name, action="stop")

  def status(self, env):
    import status_params
    from resource_management.libraries.functions.windows_service_utils import check_windows_service_status
    env.set_params(status_params)
    check_windows_service_status(status_params.nimbus_win_service_name)

if __name__ == "__main__":
  Nimbus().execute()
