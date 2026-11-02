"""Launch Gazebo, rotate_server, and square_driver to drive a square.

Usage:
    ros2 launch my_robot_nodes square.launch.py side_length:=0.8
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    side_length = ParameterValue(
        LaunchConfiguration("side_length"), value_type=float
    )

    control = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([
                FindPackageShare("diffdrive_bot"),
                "launch",
                "control.launch.py",
            ])
        ),
    )

    rotate_server = Node(
        package="my_robot_nodes",
        executable="rotate_server",
        parameters=[{"use_sim_time": True}],
        output="screen",
    )

    square_driver = Node(
        package="my_robot_nodes",
        executable="square_driver",
        parameters=[{"side_length": side_length, "use_sim_time": True}],
        output="screen",
    )

    return LaunchDescription([
        DeclareLaunchArgument(
            "side_length",
            default_value="0.5",
            description="Length of each square side, in m",
        ),
        control,
        rotate_server,
        square_driver,
    ])
