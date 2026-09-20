# RobiS Simulation

Portable ROS Noetic simulation for a four-wheel RobiS-style robot. The package
contains a Gazebo model and world, Cartographer mapping and localization,
`move_base` navigation with the A* global planner, and the TEB local planner.

## Tested Platform

- Ubuntu 20.04.6 LTS (Focal Fossa)
- ROS Noetic, `roslaunch` 1.17.0
- ARM64 (`aarch64`)
- Gazebo 11.15.1
- Cartographer ROS 1.0.0, built from source

The package uses standard ROS Noetic interfaces and is intended to work on both
ARM64 and x86_64 Ubuntu 20.04 systems. Build generated files are deliberately
excluded from the repository and must be regenerated on the target computer.

## Features

- Dimensioned four-wheel robot URDF/Xacro with a raised 2D lidar
- 10 m x 10 m Gazebo floor with walls and five traversable obstacles
- Cartographer 2D mapping and `.pbstream` localization
- Occupancy-grid export for `map_server`
- A* global planning through `global_planner/GlobalPlanner`
- Forward-biased TEB local planning
- RViz configuration for mapping and navigation
- Portable environment helper with no fixed Cartographer home-directory path

## Repository Layout

This package is normally placed at `src/robis_simulation` inside a catkin
workspace. A complete distributable workspace may use this layout:

```text
robis_sim_ws/
  src/
    CMakeLists.txt
    robis_simulation/
```

Do not upload `build/`, `devel/`, runtime logs, Python caches, or local backup
files. The included `.gitignore` excludes those artifacts.

## Dependencies

Install ROS Noetic Desktop Full first. Then install the package dependencies:

```bash
sudo apt update
sudo apt install -y \
  python3-rosdep \
  ros-noetic-xacro \
  ros-noetic-robot-state-publisher \
  ros-noetic-joint-state-publisher \
  ros-noetic-gazebo-ros \
  ros-noetic-gazebo-plugins \
  ros-noetic-rviz \
  ros-noetic-map-server \
  ros-noetic-move-base \
  ros-noetic-global-planner \
  ros-noetic-teb-local-planner \
  ros-noetic-teleop-twist-keyboard
```

Cartographer is also required. If it is available from the configured ROS
package source, install:

```bash
sudo apt install -y ros-noetic-cartographer ros-noetic-cartographer-ros
```

If Cartographer is built from source, its workspace may be located anywhere.
Before sourcing the helper, set either:

```bash
export CARTOGRAPHER_WS=/path/to/cartographer_ws
# or
export CARTOGRAPHER_SETUP=/path/to/cartographer_ws/devel_isolated/setup.bash
```

The helper also checks common locations such as `~/cartographer`,
`~/cartographer_ws`, `/opt/cartographer`, and `/usr/local/cartographer`.

## Build and Deploy

Clone or copy the repository, then build it on the target computer:

```bash
git clone https://github.com/Robify-Robotics/Robify-Robotics-RobiS.git ~/robis_sim_ws
cd ~/robis_sim_ws
source /opt/ros/noetic/setup.bash
rosdep update
rosdep install --from-paths src --ignore-src -r -y
catkin_make
```

Source the portable helper in every new terminal:

```bash
source ~/robis_sim_ws/src/robis_simulation/scripts/robis_sim_env.bash
```

The helper exports `ROBIS_SIM_WS` and sources ROS, this workspace, and a
detected or explicitly configured Cartographer workspace.

## Default Startup Behavior

Mapping and navigation start:

- Gazebo simulation server: enabled
- Gazebo graphical client: disabled
- RViz: enabled

This default is suitable for remote computers because the Gazebo graphical
client is computationally expensive. Gazebo and RViz can reduce the simulation
real-time factor, and visible pauses or slow motion are normal on lower-power
systems. Navigation performance should be evaluated using ROS timestamps and
robot motion, not only screen refresh smoothness.

Add `gazebo_gui:=true` to open the Gazebo window. For example:

```bash
roslaunch robis_simulation cartographer_mapping.launch gazebo_gui:=true
roslaunch robis_simulation navigation_cartographer_teb.launch gazebo_gui:=true
```

For remote desktop use, make sure `DISPLAY` and `XAUTHORITY` point to the active
desktop session. Both launch files accept `display` and `xauthority` arguments.

## Mapping

Start Cartographer mapping with headless Gazebo and RViz:

```bash
source ~/robis_sim_ws/src/robis_simulation/scripts/robis_sim_env.bash
roslaunch robis_simulation cartographer_mapping.launch
```

In another terminal, drive the robot:

```bash
source ~/robis_sim_ws/src/robis_simulation/scripts/robis_sim_env.bash
rosrun teleop_twist_keyboard teleop_twist_keyboard.py cmd_vel:=/cmd_vel
```

Move through the accessible corridors, observe all obstacle surfaces, and
return near the starting point to improve loop closure.

## Save the Map

Keep mapping running and execute these commands in another terminal:

```bash
source ~/robis_sim_ws/src/robis_simulation/scripts/robis_sim_env.bash

rosservice call /finish_trajectory "trajectory_id: 0"

rosservice call /write_state "filename: '${ROBIS_SIM_WS}/src/robis_simulation/maps/robis_map.pbstream'
include_unfinished_submaps: true"

rosrun cartographer_ros cartographer_pbstream_to_ros_map \
  -map_filestem=${ROBIS_SIM_WS}/src/robis_simulation/maps/robis_map \
  -pbstream_filename=${ROBIS_SIM_WS}/src/robis_simulation/maps/robis_map.pbstream \
  -resolution=0.05

sed -i 's|^image:.*|image: robis_map.pgm|' \
  "${ROBIS_SIM_WS}/src/robis_simulation/maps/robis_map.yaml"
```

Wait until all commands finish, then stop the mapping launch with `Ctrl-C`.
The relative image path in `robis_map.yaml` keeps the map portable.

## Navigation

After saving the map, start localization and navigation:

```bash
source ~/robis_sim_ws/src/robis_simulation/scripts/robis_sim_env.bash
roslaunch robis_simulation navigation_cartographer_teb.launch
```

Use `2D Nav Goal` in RViz to send a target. Cartographer maintains the
`map -> odom` transform, `global_planner/GlobalPlanner` provides A* planning,
and `teb_local_planner/TebLocalPlannerROS` controls local motion.

Useful launch overrides:

```bash
# Open the Gazebo graphical client.
roslaunch robis_simulation navigation_cartographer_teb.launch gazebo_gui:=true

# Run without RViz.
roslaunch robis_simulation navigation_cartographer_teb.launch start_rviz:=false

# Use another map and Cartographer state.
roslaunch robis_simulation navigation_cartographer_teb.launch \
  map_file:=/absolute/path/map.yaml \
  pbstream_file:=/absolute/path/map.pbstream
```

## Gazebo Only

The standalone Gazebo launch opens the Gazebo graphical client by default:

```bash
source ~/robis_sim_ws/src/robis_simulation/scripts/robis_sim_env.bash
roslaunch robis_simulation gazebo.launch
```

Run it headlessly with:

```bash
roslaunch robis_simulation gazebo.launch gui:=false
```

## Validation

Run the package-level structural validation:

```bash
python3 ~/robis_sim_ws/src/robis_simulation/test/validate_model.py
```

For a deployment check, build the workspace and launch mapping and navigation
one at a time. Confirm that `/scan`, `/map`, `/tf`, and `/cmd_vel` are present,
and stop each launch with `Ctrl-C` before starting the next one.
