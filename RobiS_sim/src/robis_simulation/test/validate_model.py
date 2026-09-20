#!/usr/bin/env python3
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET

PKG = Path(__file__).resolve().parents[1]
EXPECTED_FILES = [
    'package.xml',
    'CMakeLists.txt',
    'urdf/robis.urdf.xacro',
    'worlds/empty.world',
    'launch/gazebo.launch',
    'launch/cartographer_mapping.launch',
    'launch/move_base_teb.launch',
    'launch/navigation_cartographer_teb.launch',
    'config/cartographer_2d.lua',
    'config/move_base/costmap_common_params.yaml',
    'config/move_base/global_costmap_params.yaml',
    'config/move_base/local_costmap_params.yaml',
    'config/move_base/move_base_params.yaml',
    'config/move_base/teb_local_planner_params.yaml',
    'scripts/robis_sim_env.bash',
]

EXPECTED_TEXT = {
    'urdf/robis.urdf.xacro': [
        'libgazebo_ros_skid_steer_drive.so',
        'libgazebo_ros_laser.so',
    ],
    'config/move_base/move_base_params.yaml': [
        'base_global_planner: "global_planner/GlobalPlanner"',
        'base_local_planner: "teb_local_planner/TebLocalPlannerROS"',
        'use_dijkstra: false',
        'planner_frequency: 0.0',
    ],
    'config/move_base/teb_local_planner_params.yaml': [
        'max_samples: 120',
        'penalty_epsilon: 0.01',
        'enable_homotopy_class_planning: false',
        'enable_multithreading: false',
    ],
    'config/cartographer_2d.lua': [
        'tracking_frame = "base_link"',
        'published_frame = "odom"',
        'use_odometry = false',
        'num_laser_scans = 1',
    ],
    'launch/cartographer_mapping.launch': [
        'cartographer_node',
        'occupancy_grid_node',
        '<arg name="gazebo_gui" default="false"/>',
    ],
    'launch/move_base_teb.launch': [
        'map_server',
        'move_base',
    ],
    'launch/navigation_cartographer_teb.launch': [
        '<arg name="start_gazebo" default="true"/>',
        '<arg name="gazebo_gui" default="false"/>',
        '<arg name="start_rviz" default="true"/>',
    ],
}

EXPECTED_WORLD_POSES = {
    'box_obstacle_1': '1.45 1.45 0.25 0 0 0.35',
    'box_obstacle_2': '-1.40 -1.40 0.20 0 0 -0.55',
    'box_obstacle_3': '-1.45 1.45 0.25 0 0 0.15',
    'box_obstacle_4': '1.35 -1.55 0.25 0 0 -0.25',
    'box_obstacle_6': '0.0 -1.90 0.20 0 0 0',
}

EXPECTED_XACRO_PROPERTIES = {
    'body_length': '0.4235',
    'body_width': '0.268',
    'body_height': '0.06678',
    'wheel_radius': '0.063',
    'wheel_width': '0.041',
    'wheel_x': '0.152',
    'wheel_y': '0.154',
    'lidar_x': '0.135',
    'lidar_radius': '0.051',
    'lidar_height': '0.085',
    'riser_height': '0.174',
}

errors = []
for rel in EXPECTED_FILES:
    if not (PKG / rel).is_file():
        errors.append(f'missing file: {rel}')

for rel, snippets in EXPECTED_TEXT.items():
    path = PKG / rel
    if not path.is_file():
        continue
    text = path.read_text(errors='replace')
    for snippet in snippets:
        if snippet not in text:
            errors.append(f'{rel} missing snippet: {snippet}')

world = PKG / 'worlds/empty.world'
if world.is_file():
    try:
        models = {
            model.attrib.get('name'): (model.findtext('pose') or '').strip()
            for model in ET.parse(world).getroot().findall('.//world/model')
        }
        if 'box_obstacle_5' in models:
            errors.append('world should not contain box_obstacle_5')
        for name, expected_pose in EXPECTED_WORLD_POSES.items():
            if models.get(name) != expected_pose:
                errors.append(
                    f'world model {name} pose should be {expected_pose}, '
                    f'got {models.get(name)!r}'
                )
    except ET.ParseError as error:
        errors.append(f'world XML parse failed: {error}')

urdf = PKG / 'urdf/robis.urdf.xacro'
if urdf.is_file():
    text = urdf.read_text(errors='replace')
    for name, value in EXPECTED_XACRO_PROPERTIES.items():
        pattern = rf'<xacro:property\s+name="{re.escape(name)}"\s+value="{re.escape(value)}"\s*/>'
        if not re.search(pattern, text):
            errors.append(f'urdf property {name} should be {value}')
    for prefix in ['front_left', 'front_right', 'rear_left', 'rear_right']:
        if f'prefix="{prefix}"' not in text:
            errors.append(f'urdf missing wheel macro call: {prefix}')
        if f'{prefix}_wheel_joint' not in text:
            errors.append(f'urdf missing wheel joint: {prefix}_wheel_joint')
    for link in ['base_footprint', 'base_link', 'lidar_riser_link', 'laser_link']:
        if f'name="{link}"' not in text:
            errors.append(f'urdf missing link: {link}')

if errors:
    print('VALIDATION FAILED')
    for error in errors:
        print('-', error)
    sys.exit(1)
print('VALIDATION PASSED')
