# Copyright 2024 Husarion sp. z o.o.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import yaml
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    OpaqueFunction,
)

from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, EnvironmentVariable


def get_value(node: yaml.Node, key: str):
    try:
        value = node[key]
        if value == "None":
            value = ""
        return value

    except KeyError:
        return ""


def get_launch_description(name: str, package: str, namespace: str, component: yaml.Node):
    return IncludeLaunchDescription(
        PythonLaunchDescriptionSource([package, "/launch/gz_", name, ".launch.py"]),
        launch_arguments={
            "robot_namespace": namespace,
            "device_namespace": get_value(component, "namespace"),
            "tf_prefix": get_value(component, "tf_prefix"),
            "gz_bridge_name": component["namespace"][1:] + "_gz_bridge",
            "camera_name": get_value(component, "name"),
        }.items(),
    )


def get_launch_descriptions_from_yaml_node(
    node: yaml.Node, package: os.PathLike, namespace: str
) -> IncludeLaunchDescription:
    actions = []
    for component in node["components"]:
        if component["type"] == "LDR01" or component["type"] == "LDR06":
            actions.append(get_launch_description("slamtec_rplidar", package, namespace, component))

        if component["type"] == "LDR13":
            actions.append(get_launch_description("ouster_os", package, namespace, component))

        if component["type"] == "LDR20":
            actions.append(get_launch_description("velodyne", package, namespace, component))

        if component["type"] == "CAM01":
            actions.append(get_launch_description("orbbec_astra", package, namespace, component))

        if component["type"] == "MAN01" or component["type"] == "MAN02":
            actions.append(get_launch_description("ur", package, namespace, component))

        if (
            component["type"] == "MAN04"
            # or component["type"] == "MAN03" # sim_isaac error
            or component["type"] == "MAN05"
            or component["type"] == "MAN06"
            or component["type"] == "MAN07"
        ):
            actions.append(get_launch_description("kinova", package, namespace, component))

    return actions


def launch_setup(context, *args, **kwargs):
    ros_components_description = get_package_share_directory("ros_components_description")

    components_config_path = LaunchConfiguration("components_config_path").perform(context)
    namespace = LaunchConfiguration("namespace").perform(context)

    components_config = None
    if components_config_path == "None":
        return []

    with open(os.path.join(components_config_path), 'r') as file:
        components_config = yaml.safe_load(file)

    actions = []
    if components_config != None:
        actions += get_launch_descriptions_from_yaml_node(
            components_config, ros_components_description, namespace
        )

    return actions


def generate_launch_description():
    declare_components_config_path_arg = DeclareLaunchArgument(
        "components_config_path",
        default_value="None",
        description=(
            "Additional components configuration file. Components described in this file "
            "are dynamically included in Panther's urdf."
            "Panther options are described here "
            "https://husarion.com/manuals/panther/panther-options/"
        ),
    )

    declare_namespace_arg = DeclareLaunchArgument(
        "namespace",
        default_value=EnvironmentVariable("ROBOT_NAMESPACE", default_value=""),
        description="Add namespace to all launched nodes",
    )

    actions = [
        declare_components_config_path_arg,
        declare_namespace_arg,
        OpaqueFunction(function=launch_setup),
    ]

    return LaunchDescription(actions)
