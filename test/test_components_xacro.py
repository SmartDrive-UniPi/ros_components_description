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


import xml.dom
import xml.dom.minidom
import os
import xacro
import xml
import yaml
from ament_index_python.packages import get_package_share_directory

ros_components_description = get_package_share_directory("ros_components_description")
xacro_path = os.path.join(ros_components_description, "test/component.urdf.xacro")

# Type: [model_link, sensor_link, sensor_name]
components_types_with_names = {
    "LDR01": ["slamtec_rplidar_s1", "laser", "slamtec_rplidar_s1_sensor"],
    "LDR06": ["slamtec_rplidar_s3", "laser", "slamtec_rplidar_s3_sensor"],
    "LDR13": ["ouster_os1_32", "os_lidar", "ouster_os1_32_sensor"],
    "LDR20": ["velodyne_puck", "velodyne", "velodyne_puck_sensor"],
    "CAM01": ["orbbec_astra", "orbbec_astra", "orbbec_astra_color"],
}


class ComponentsYamlParseUtils:
    __test__ = False

    def __init__(self, components_config_path: str) -> None:
        self.components_config_path = components_config_path
        self._urdf = xml.dom.minidom.Document()

    def save_yaml(self, node: yaml.Node) -> None:
        with open(self.components_config_path, mode="w", encoding="utf-8") as file:
            yaml.dump(node, file, default_flow_style=False)

    def create_component(
        self,
        type: str,
        device_namespace: str,
        parent_link="cover_link",
        xyz="0.0 0.0 0.0",
        rpy="0.0 0.0 0.0",
    ) -> dict:
        return {
            "type": type,
            "parent_link": parent_link,
            "xyz": xyz,
            "rpy": rpy,
            "device_namespace": device_namespace,
        }

    def does_urdf_parse(self) -> bool:
        try:
            self._urdf = xacro.process_file(
                xacro_path, mappings={"components_config_path": self.components_config_path}
            )
        except xacro.XacroException as e:
            return False
        return True

    def does_link_exist(self, doc: xml.dom.minidom.Document, link_name: str) -> bool:
        links = doc.getElementsByTagName('link')
        for link in links:
            if link.getAttribute('name') == link_name:
                return True
        return False

    def does_sensor_name_exist(
        self, doc: xml.dom.minidom.Document, link_name: str, sensor_name: str
    ) -> bool:
        gazebos_tags = doc.getElementsByTagName('gazebo')
        for tag in gazebos_tags:
            if tag.getAttribute('reference') == link_name:
                sensors = doc.getElementsByTagName('sensor')
                for sensor in sensors:
                    if sensor.getAttribute('name') == sensor_name:
                        return True

        return False

    def test_component(self, component: dict, expected_result: list, components_config_path: str):
        names = components_types_with_names[component["type"]]
        component_name = names[0]
        sensor_reference = names[1]
        sensor_name = names[2]

        device_namespace = component["device_namespace"]
        link_name = device_namespace + "_" + component_name + "_link"
        sensor_name = device_namespace + "_" + sensor_name
        sensor_link_name = device_namespace + "_" + sensor_reference

        if self.does_urdf_parse() != expected_result[0]:
            assert (
                False
            ), f"Expected prase result {expected_result[0]} with file {components_config_path} and component {component_name}."

        if self.does_link_exist(self._urdf, link_name) != expected_result[1]:
            assert (
                False
            ), f"Link name: {link_name}. Expected result {expected_result[1]} with file {components_config_path} and component {component_name}."

        if (
            self.does_sensor_name_exist(self._urdf, sensor_link_name, sensor_name)
            != expected_result[2]
        ):
            assert (
                False
            ), f"Sensor name: {sensor_name}, sensor link name: {sensor_link_name}. Expected result {expected_result[2]} with file {components_config_path} and component {component_name}."


def test_all_good_single_components(tmpdir_factory):
    for type_name, value in components_types_with_names.items():
        name = value[0]
        dir = tmpdir_factory.mktemp(name)
        components_config_path = dir.join(name + "_test_components.yaml")

        utils = ComponentsYamlParseUtils(str(components_config_path))
        components = {
            "components": [utils.create_component(type_name, name)],
        }

        utils.save_yaml(components)

        for component in components["components"]:
            utils.test_component(component, [True, True, True], str(components_config_path))


