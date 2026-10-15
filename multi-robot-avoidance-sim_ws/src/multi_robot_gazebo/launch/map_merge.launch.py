from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    use_sim_time = LaunchConfiguration('use_sim_time', default='true')

    return LaunchDescription([
        DeclareLaunchArgument('use_sim_time', default_value='true'),

        Node(
            package='multirobot_map_merge',
            executable='map_merge',
            name='map_merge',
            output='screen',
            parameters=[{
                'use_sim_time': use_sim_time,
                'world_frame': 'map',
                'robot_namespaces': ['robot1', 'robot2'],
                'known_init_poses': False,
                'merging_rate': 5.0,
                'discovery_rate': 0.05,
                'estimation_rate': 5.0,
                'estimation_confidence': 0.8,
            }],
        ),
    ])