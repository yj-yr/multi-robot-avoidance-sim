# Multi-Robot Simulation Workspace

多机器人相关仿真集合。每个仿真独立成一个子目录，放在 `src/` 下，互不干扰，可单独运行。

---

## 项目列表

| 仿真 | 类型 | 说明 |
|---|---|---|
| [two_robot_avoidance](src/two_robot_avoidance/) | 纯 Python | 两台机器人预测式协同避障 |
| [multi_robot_gazebo](src/multi_robot_gazebo/) | ROS2 + Gazebo | 命名空间双机器人 Gazebo + RViz 仿真 |

---

## 目录结构

```text
multi-robot-avoidance-sim_ws/
├── README.md
├── LICENSE
├── requirements.txt
├── .gitignore
└── src/
    ├── other/
    │   └── .gitkeep
    ├── two_robot_avoidance/
    │   ├── README.md
    │   └── simulate.py
    └── multi_robot_gazebo/
        ├── README.md
        ├── package.xml
        ├── CMakeLists.txt
        ├── launch/
        │   └── multi_robot.launch.py
        ├── urdf/
        │   └── diff_robot.urdf.xacro
        ├── worlds/
        │   └── empty.world
        └── rviz/
            └── multi_robot.rviz
```

---

## 环境要求

### 通用

- Python 3.10+
- numpy
- matplotlib

### multi_robot_gazebo 额外需要

- ROS2 Humble
- Gazebo Classic 11
- `gazebo_ros`、`robot_state_publisher`、`xacro`、`rviz2`
- `teleop_twist_keyboard`（可选，键盘控制用）

安装 Python 依赖：

```bash
pip install -r requirements.txt
```

---

## 快速开始

### 1. two_robot_avoidance（纯 Python）

不需要 ROS2，任何有 Python 的机器都能跑：

```bash
pip install -r requirements.txt
python3 src/two_robot_avoidance/simulate.py
```

弹出窗口后，可看到两台机器人从不同起点出发，接近时一台停车让行，另一台通过后恢复。

### 2. multi_robot_gazebo（ROS2 + Gazebo）

需要先编译：

```bash
cd ~/multi-robot-avoidance-sim/multi-robot-avoidance-sim_ws
colcon build --packages-select multi_robot_gazebo
source install/setup.bash
```

启动仿真：

```bash
ros2 launch multi_robot_gazebo multi_robot.launch.py
```

会依次启动 Gazebo、spawn 两台差速小车、启动 RViz。

键盘控制 robot1：

```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard \
  --ros-args -r /cmd_vel:=/robot1/cmd_vel
```

键盘控制 robot2（另开终端）：

```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard \
  --ros-args -r /cmd_vel:=/robot2/cmd_vel
```

---

## 各仿真说明

### two_robot_avoidance

| 项目 | 说明 |
|---|---|
| 语言 | 纯 Python |
| 依赖 | numpy、matplotlib |
| 入口 | `simulate.py` |
| 可视化 | matplotlib 动画 |
| 核心逻辑 | 预测未来 3 秒轨迹 → 算最小预测距离 → 小于 0.8m 时编号大的让行 |

### multi_robot_gazebo

| 项目 | 说明 |
|---|---|
| 语言 | Python + xacro + URDF |
| 依赖 | ROS2 Humble + Gazebo Classic |
| 入口 | `launch/multi_robot.launch.py` |
| 可视化 | RViz + Gazebo |
| 核心逻辑 | 命名空间隔离、独立话题、独立 TF 树、双机同场景运行 |

---

## 命名空间约定

`multi_robot_gazebo` 中每台机器人独立命名空间：

| 机器人 | 命名空间 | TF 前缀 |
|---|---|---|
| robot1 | `/robot1` | `robot1_` |
| robot2 | `/robot2` | `robot2_` |

话题示例：

```text
/robot1/cmd_vel
/robot1/odom
/robot1/scan
/robot2/cmd_vel
/robot2/odom
/robot2/scan
```

以后新增机器人，只需在 `launch/multi_robot.launch.py` 的 `ROBOTS` 列表加一行。

---

## 如何新增一个仿真

1. 在 `src/` 下建目录：

    mkdir -p src/新仿真名

2. 放入入口脚本和该仿真自己的 `README.md`

3. 在根 README 的“项目列表”里加一行

4. 提交：

    git add .
    git commit -m "feat: 添加 XXX 仿真"
    git push

**规则**：

- 每个仿真一个目录，入口脚本统一叫 `simulate.py` 或 `main.py`
- 每个仿真配一个小 README
- 公共代码等重复 3 次以上再抽到 `src/common/`

---

## 常见问题

| 问题 | 解决 |
|---|---|
| `ModuleNotFoundError: numpy` | `pip install -r requirements.txt` |
| Gazebo 里车不动 | 点一下 Gazebo 界面，按空格取消暂停 |
| RViz 里看不到模型 | Fixed Frame 改成 `robot1_odom` |
| TF 帧名双前缀 | 删掉 launch 里的 `frame_prefix` 参数 |
| `no upstream branch` | `git push -u origin main`（只需一次） |
| `rejected ... fetch first` | 先 `git pull` 再 `git push` |

---

## 许可

MIT License

---

## 作者

杨静