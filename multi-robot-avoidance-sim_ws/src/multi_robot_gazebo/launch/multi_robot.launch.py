import os
from launch import LaunchDescription
from launch.actions import (
    IncludeLaunchDescription, GroupAction, TimerAction
)
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command
from launch_ros.actions import Node, PushRosNamespace
from ament_index_python.packages import get_package_share_directory

ROBOTS = [
    {'name': 'robot1', 'x': '-1.5', 'y': '0', 'yaw': '0.0'},
    {'name': 'robot2', 'x': '1.5',  'y': '0', 'yaw': '3.14159'},
]


def spawn_robot(robot):
    pkg = get_package_share_directory('multi_robot_gazebo')
    urdf_file = os.path.join(pkg, 'urdf', 'diff_robot.urdf.xacro')

    robot_desc = Command([
        'xacro ', urdf_file,
        ' robot_name:=', robot['name'],
        ' prefix:=', robot['name'] + '_',
    ])

    ns = robot['name']

    return GroupAction([
        PushRosNamespace(ns),
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            parameters=[{
                'robot_description': robot_desc,
            }],
            output='screen',
        ),
        # map -> robotN_map 的静态 TF（关键：让 map 帧存在）
        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            name=f'{ns}_map_to_local_map',
            arguments=[
                '--x', robot['x'],
                '--y', robot['y'],
                '--z', '0',
                '--yaw', robot['yaw'],
                '--pitch', '0',
                '--roll', '0',
                '--frame-id', 'map',
                '--child-frame-id', f'{ns}_map',
            ],
            output='screen',
        ),
        Node(
            package='gazebo_ros',
            executable='spawn_entity.py',
            arguments=[
                '-topic', 'robot_description',
                '-entity', ns,
                '-x', robot['x'],
                '-y', robot['y'],
                '-Y', robot['yaw'],
            ],
            output='screen',
        ),
    ])


def generate_launch_description():
    pkg = get_package_share_directory('multi_robot_gazebo')

    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory('gazebo_ros'),
                'launch', 'gazebo.launch.py'
            )
        ),
        launch_arguments={
            'world': os.path.join(pkg, 'worlds', 'walls.world'),
            'verbose': 'false',
        }.items(),
    )

    actions = [gazebo]
    for i, r in enumerate(ROBOTS):
        actions.append(TimerAction(period=2.0 + i * 2.0,
                                   actions=[spawn_robot(r)]))

    actions.append(TimerAction(
        period=6.0,
        actions=[Node(
            package='rviz2',
            executable='rviz2',
            arguments=['-d', os.path.join(pkg, 'rviz', 'multi_robot.rviz')],
            output='screen',
        )],
    ))

    return LaunchDescription(actions)