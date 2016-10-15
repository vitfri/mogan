# Copyright 2016 Huawei Technologies Co.,LTD.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from ironicclient import exceptions as client_e
from oslo_log import log as logging

from nimble.common.i18n import _LE
from nimble.common import ironic
from nimble.engine.baremetal import ironic_states

LOG = logging.getLogger(__name__)

_NODE_FIELDS = ('uuid', 'power_state', 'target_power_state', 'provision_state',
                'target_provision_state', 'last_error', 'maintenance',
                'properties', 'instance_uuid')


def get_ports_from_node(node_uuid, detail=False):
    """List the MAC addresses and the port types from a node."""
    ironicclient = ironic.IronicClientWrapper()
    ports = ironicclient.call("node.list_ports", node_uuid, detail=detail)
    return ports


def plug_vif(ironic_port_id, port_id):
    ironicclient = ironic.IronicClientWrapper()
    patch = [{'op': 'add',
              'path': '/extra/vif_port_id',
              'value': port_id}]
    ironicclient.call("port.update", ironic_port_id, patch)


def unplug_vif(ironic_port_id):
    ironicclient = ironic.IronicClientWrapper()
    patch = [{'op': 'remove',
              'path': '/extra/vif_port_id'}]
    try:
        ironicclient.call("port.update", ironic_port_id, patch)
    except client_e.BadRequest:
        pass


def set_instance_info(instance):
    ironicclient = ironic.IronicClientWrapper()

    patch = []
    # Associate the node with an instance
    patch.append({'path': '/instance_uuid', 'op': 'add',
                  'value': instance.uuid})
    # Add the required fields to deploy a node.
    patch.append({'path': '/instance_info/image_source', 'op': 'add',
                  'value': instance.image_uuid})
    patch.append({'path': '/instance_info/root_gb', 'op': 'add',
                  'value': '10'})
    patch.append({'path': '/instance_info/swap_mb', 'op': 'add',
                  'value': '0'})
    patch.append({'path': '/instance_info/display_name',
                  'op': 'add', 'value': instance.name})
    patch.append({'path': '/instance_info/vcpus', 'op': 'add',
                  'value': '1'})
    patch.append({'path': '/instance_info/memory_mb', 'op': 'add',
                  'value': '10240'})
    patch.append({'path': '/instance_info/local_gb', 'op': 'add',
                  'value': '10'})

    ironicclient.call("node.update", instance.node_uuid, patch)


def do_node_deploy(node_uuid):
    # trigger the node deploy
    ironicclient = ironic.IronicClientWrapper()
    ironicclient.call("node.set_provision_state", node_uuid,
                      ironic_states.ACTIVE)


def get_node_by_instance(instance_uuid):
    ironicclient = ironic.IronicClientWrapper()
    return ironicclient.call('node.get_by_instance_uuid',
                             instance_uuid, fields=_NODE_FIELDS)


def destroy_node(node_uuid):
    # trigger the node destroy
    ironicclient = ironic.IronicClientWrapper()
    ironicclient.call("node.set_provision_state", node_uuid,
                      ironic_states.DELETED)


def validate_node(node_uuid):
    ironicclient = ironic.IronicClientWrapper()
    ironicclient.call("node.validate", node_uuid)


def get_node_list(**kwargs):
    """Helper function to return the list of nodes.

    If unable to connect ironic server, an empty list is returned.

    :returns: a list of raw node from ironic

    """
    ironicclient = ironic.IronicClientWrapper()
    try:
        node_list = ironicclient.call("node.list", **kwargs)
    except client_e.ClientException as e:
        LOG.exception(_LE("Could not get nodes from ironic. Reason: "
                          "%(detail)s"), {'detail': e.message})
        node_list = []
    return node_list


def get_node_states(node_uuid):
    ironicclient = ironic.IronicClientWrapper()
    return ironicclient.call("node.states", node_uuid)
    # Do we need to catch NotFound exception.


def set_power_state(node_uuid, state):
    ironicclient = ironic.IronicClientWrapper()
    ironicclient.call("node.set_power_state", node_uuid, state)
    # Do we need to catch NotFound exception.