#!/usr/bin/env python3
#
# Copyright 2019 ROBOTIS CO., LTD.
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
#
# Authors: Joep Tool

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (DeclareLaunchArgument, IncludeLaunchDescription,
                            SetEnvironmentVariable)
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch.conditions import UnlessCondition
from launch_ros.actions import Node


def generate_launch_description():
    pkg_gazebo_ros = get_package_share_directory('gazebo_ros')
    pkg_hbot_simulation = get_package_share_directory('hbot_simulation')
    pkg_hbot_description = get_package_share_directory('hbot_description')

    use_sim_time = LaunchConfiguration('use_sim_time')
    x_pose = LaunchConfiguration('x_pose')
    y_pose = LaunchConfiguration('y_pose')
    headless = LaunchConfiguration('headless')

    world = os.path.join(pkg_hbot_simulation, 'worlds', 'hbot_house.world')

    # robot_state_publisher publishes this URDF *and* Gazebo spawns from it (via
    # -topic below), so the simulated body and the TF tree can never drift apart.
    urdf_path = os.path.join(pkg_hbot_description, 'urdf', 'hbot.urdf')
    with open(urdf_path, 'r') as infp:
        robot_desc = infp.read()

    declare_use_sim_time_cmd = DeclareLaunchArgument(
        'use_sim_time', default_value='true',
        description='Use the Gazebo /clock as the ROS time source')
    declare_x_pose_cmd = DeclareLaunchArgument(
        'x_pose', default_value='-1.0', description='Robot spawn X (m)')
    declare_y_pose_cmd = DeclareLaunchArgument(
        'y_pose', default_value='-4.5', description='Robot spawn Y (m)')
    declare_headless_cmd = DeclareLaunchArgument(
        'headless', default_value='false',
        description='Run gzserver only, without the gzclient GUI')

    # Let Gazebo resolve `model://hbot_house` and friends from this package.
    set_model_path = SetEnvironmentVariable(
        name='GAZEBO_MODEL_PATH',
        value=[os.path.join(pkg_hbot_simulation, 'models'), ':',
               os.environ.get('GAZEBO_MODEL_PATH', '')])

    gzserver_cmd = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_gazebo_ros, 'launch', 'gzserver.launch.py')
        ),
        launch_arguments={'world': world}.items()
    )

    gzclient_cmd = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_gazebo_ros, 'launch', 'gzclient.launch.py')
        ),
        condition=UnlessCondition(headless)
    )

    robot_state_publisher_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='screen',
        parameters=[{'use_sim_time': use_sim_time,
                     'robot_description': robot_desc}],
    )

    # Spawn from the published /robot_description rather than a pre-baked .sdf so
    # there is a single source of truth (the xacro-generated URDF).
    spawn_hbot_cmd = Node(
        package='gazebo_ros',
        executable='spawn_entity.py',
        output='screen',
        arguments=[
            '-entity', 'hbot',
            '-topic', 'robot_description',
            '-x', x_pose,
            '-y', y_pose,
            '-z', '0.01',
        ],
    )

    ld = LaunchDescription()

    ld.add_action(declare_use_sim_time_cmd)
    ld.add_action(declare_x_pose_cmd)
    ld.add_action(declare_y_pose_cmd)
    ld.add_action(declare_headless_cmd)

    ld.add_action(set_model_path)
    ld.add_action(gzserver_cmd)
    ld.add_action(gzclient_cmd)
    ld.add_action(robot_state_publisher_node)
    ld.add_action(spawn_hbot_cmd)

    return ld
