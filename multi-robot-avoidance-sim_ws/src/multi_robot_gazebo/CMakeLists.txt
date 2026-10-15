cmake_minimum_required(VERSION 3.8)
project(multi_robot_gazebo)

find_package(ament_cmake REQUIRED)

install(DIRECTORY urdf launch worlds rviz maps
  DESTINATION share/${PROJECT_NAME})

ament_package()
