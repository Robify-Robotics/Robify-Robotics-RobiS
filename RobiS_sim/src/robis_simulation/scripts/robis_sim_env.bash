#!/usr/bin/env bash
# Source this file before launching RobiS simulation commands.
# It derives the catkin workspace from this package path and lets Cartographer
# live in a standard install, a user-selected workspace, or a source build.

set -e

if [ -f /opt/ros/noetic/setup.bash ]; then
  source /opt/ros/noetic/setup.bash
else
  echo "[robis_sim_env] ROS Noetic setup not found at /opt/ros/noetic/setup.bash" >&2
  return 1 2>/dev/null || exit 1
fi

_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
_ROBIS_WS="$(cd "${_SCRIPT_DIR}/../../.." && pwd)"
_ROBIS_SETUP="${_ROBIS_WS}/devel/setup.bash"

_source_robis_ws() {
  if [ -f "${_ROBIS_SETUP}" ]; then
    source "${_ROBIS_SETUP}"
  fi
}

_find_cartographer_setup() {
  if [ -n "${CARTOGRAPHER_SETUP:-}" ] && [ -f "${CARTOGRAPHER_SETUP}" ]; then
    printf '%s\n' "${CARTOGRAPHER_SETUP}"
    return 0
  fi

  if [ -n "${CARTOGRAPHER_WS:-}" ]; then
    for candidate in \
      "${CARTOGRAPHER_WS}/install_isolated/setup.bash" \
      "${CARTOGRAPHER_WS}/devel_isolated/setup.bash" \
      "${CARTOGRAPHER_WS}/install/setup.bash" \
      "${CARTOGRAPHER_WS}/devel/setup.bash"; do
      if [ -f "${candidate}" ]; then
        printf '%s\n' "${candidate}"
        return 0
      fi
    done
  fi

  for base in \
    "${HOME}/cartographer" \
    "${HOME}/cartographer_ws" \
    "/opt/cartographer" \
    "/usr/local/cartographer"; do
    for candidate in \
      "${base}/install_isolated/setup.bash" \
      "${base}/devel_isolated/setup.bash" \
      "${base}/install/setup.bash" \
      "${base}/devel/setup.bash"; do
      if [ -f "${candidate}" ]; then
        printf '%s\n' "${candidate}"
        return 0
      fi
    done
  done

  return 1
}

_add_cartographer_source_tree() {
  local base
  for base in \
    "${CARTOGRAPHER_WS:-}" \
    "${HOME}/cartographer" \
    "${HOME}/cartographer_ws" \
    "/opt/cartographer" \
    "/usr/local/cartographer"; do
    [ -n "${base}" ] || continue
    if [ -d "${base}/src/cartographer_ros" ]; then
      export ROS_PACKAGE_PATH="${base}/src/cartographer_ros/cartographer_rviz:${base}/src/cartographer_ros/cartographer_ros:${base}/src/cartographer_ros/cartographer_ros_msgs:${ROS_PACKAGE_PATH}"
    fi
    if [ -d "${base}/src/cartographer" ]; then
      export ROS_PACKAGE_PATH="${base}/src/cartographer:${ROS_PACKAGE_PATH}"
    fi
    if [ -d "${base}/devel_isolated" ]; then
      export CMAKE_PREFIX_PATH="${base}/devel_isolated/cartographer_rviz:${base}/devel_isolated/cartographer_ros:${base}/devel_isolated/cartographer_ros_msgs:${base}/devel_isolated/ceres-solver:${base}/devel_isolated/cartographer:${CMAKE_PREFIX_PATH}"
      export LD_LIBRARY_PATH="${base}/devel_isolated/cartographer/lib:${base}/devel_isolated/ceres-solver/lib:${LD_LIBRARY_PATH}"
      export PYTHONPATH="${base}/devel_isolated/cartographer_ros/lib/python3/dist-packages:${base}/devel_isolated/cartographer_ros_msgs/lib/python3/dist-packages:${PYTHONPATH}"
    fi
  done
}

_source_robis_ws

if ! rospack find cartographer_ros >/dev/null 2>&1; then
  if _CARTO_SETUP="$(_find_cartographer_setup)"; then
    source "${_CARTO_SETUP}"
    _source_robis_ws
  fi
fi

if ! rospack find cartographer_ros >/dev/null 2>&1; then
  _add_cartographer_source_tree
fi

if ! rospack find cartographer_ros >/dev/null 2>&1; then
  cat >&2 <<'EOM'
[robis_sim_env] cartographer_ros was not found.
Install ros-noetic-cartographer-ros if available, or point this script to a
Cartographer workspace before sourcing it, for example:

  export CARTOGRAPHER_WS=/path/to/cartographer_ws
  # or
  export CARTOGRAPHER_SETUP=/path/to/cartographer_ws/devel_isolated/setup.bash
  source path/to/robis_simulation/scripts/robis_sim_env.bash
EOM
fi

export ROBIS_SIM_WS="${_ROBIS_WS}"
unset _SCRIPT_DIR _ROBIS_WS _ROBIS_SETUP _CARTO_SETUP
