# Multi-Robot Gazebo Simulation

基于 ROS2 Humble + Gazebo Classic 11 的双机器人命名空间仿真。

两台差速小车在同一室内房间中运行，各自拥有独立话题、TF 树和传感器，
通过命名空间隔离，可在 RViz 中同时可视化，并支持双机独立 SLAM 建图。

---

## 一、效果

- Gazebo 室内房间场景中生成两台差速小车
- robot1 与 robot2 各自独立命名空间
- 每台车带激光雷达、里程计、差速驱动插件
- 所有话题、TF 帧均在命名空间下，互不干扰
- RViz 同时显示两台车的模型、激光、地图
- 每台车独立运行 slam_toolbox 建图
- 双机地图分别保存为 Nav2 可用格式

---

## 二、目录结构

```text
multi_robot_gazebo/
├── package.xml
├── CMakeLists.txt
├── README.md
├── launch/
│   ├── multi_robot.launch.py      # 一键启动 Gazebo + 两机 + RViz
│   └── map_merge.launch.py        # 多机地图合并（实验性）
├── urdf/
│   └── diff_robot.urdf.xacro      # 差速小车模型，支持 robot_name / prefix 参数
├── worlds/
│   ├── empty.world                # 空地 + 太阳光 + 地面
│   └── walls.world                # 室内房间场景
├── rviz/
│   └── multi_robot.rviz           # 双机可视化配置（双 Map + 双 Laser + Merged）
└── maps/                          # 保存的地图
    ├── robot1_map.pgm
    ├── robot1_map.yaml
    ├── robot2_map.pgm
    ├── robot2_map.yaml
    └── merged_map.pgm / .yaml     # 合并结果（实验性，未完全对齐）
```

---

## 三、依赖

### 必需

- ROS2 Humble
- Gazebo Classic 11
- gazebo_ros
- robot_state_publisher
- xacro
- rviz2
- slam_toolbox
- nav2_map_server

### 可选

- teleop_twist_keyboard：键盘控制
- multirobot_map_merge：合并多机地图

安装：

```bash
sudo apt install ros-humble-gazebo-ros-pkgs \
                 ros-humble-robot-state-publisher \
                 ros-humble-xacro \
                 ros-humble-rviz2 \
                 ros-humble-slam-toolbox \
                 ros-humble-teleop-twist-keyboard \
                 ros-humble-nav2-map-server
```

---

## 四、编译

```bash
cd ~/multi-robot-avoidance-sim/multi-robot-avoidance-sim_ws
colcon build --symlink-install --packages-select multi_robot_gazebo
source install/setup.bash
```

> 用 `--symlink-install`，以后改 launch / rviz / urdf 不用重编。

---

## 五、运行仿真

```bash
ros2 launch multi_robot_gazebo multi_robot.launch.py
```

启动流程：

1. Gazebo 弹出场景
2. 2 秒后 spawn robot1
3. 4 秒后 spawn robot2
4. 6 秒后启动 RViz

> Gazebo 里车不动？点一下 Gazebo 窗口，按空格取消暂停。

---

## 六、命名空间与 TF 结构

| 机器人 | 命名空间 | TF 帧前缀 | 初始位置 | 初始朝向 |
|---|---|---|---|---|
| robot1 | /robot1 | robot1_ | (-1.5, 0) | 0° |
| robot2 | /robot2 | robot2_ | (1.5, 0) | 180° |

两车初始位置在 `launch/multi_robot.launch.py` 的 `ROBOTS` 列表中修改。

### TF 树

```text
map                                    ← Gazebo 世界坐标，由 static TF 固定
├── robot1_map                         ← SLAM 局部地图坐标系
│   └── robot1_odom
│       └── robot1_base_link
│           ├── robot1_caster_wheel
│           ├── robot1_lidar_link
│           ├── robot1_left_wheel
│           └── robot1_right_wheel
└── robot2_map
    └── robot2_odom
        └── robot2_base_link
            ├── robot2_caster_wheel
            ├── robot2_lidar_link
            ├── robot2_left_wheel
            └── robot2_right_wheel
```

**关键**：

- `map -> robotN_map`：由 launch 里 `static_transform_publisher` 发布，固定值 = Gazebo 初始位置
- `robotN_map -> robotN_odom`：由 slam_toolbox 发布，动态，会漂移
- `robotN_odom -> robotN_base_link`：由 Gazebo diff_drive 插件发布

**不要**在 launch 里用 `static_transform_publisher` 发 `map -> robotN_odom`，会和 slam_toolbox 冲突。

---

## 七、话题列表

```bash
ros2 topic list | grep robot
```

预期输出：

```text
/robot1/cmd_vel
/robot1/joint_states
/robot1/odom
/robot1/robot_description
/robot1/scan
/robot2/cmd_vel
/robot2/joint_states
/robot2/odom
/robot2/robot_description
/robot2/scan
```

---

## 八、键盘控制

### 控制 robot1

```bash
source ~/multi-robot-avoidance-sim/multi-robot-avoidance-sim_ws/install/setup.bash

ros2 run teleop_twist_keyboard teleop_twist_keyboard \
  --ros-args -r /cmd_vel:=/robot1/cmd_vel
```

### 控制 robot2

```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard \
  --ros-args -r /cmd_vel:=/robot2/cmd_vel
```

按键：`i` 前进，`j` 左转，`l` 右转，`,` 后退，`k` 停。

---

## 九、直接发速度指令

```bash
# robot1 前进
ros2 topic pub /robot1/cmd_vel geometry_msgs/msg/Twist \
  "{linear: {x: 0.3}, angular: {z: 0.0}}" -r 10

# robot2 转圈
ros2 topic pub /robot2/cmd_vel geometry_msgs/msg/Twist \
  "{linear: {x: 0.0}, angular: {z: 0.5}}" -r 10
```

---

## 十、TF 树验证

```bash
ros2 run tf2_tools view_frames
evince frames.pdf
```

应看到 `map` 下两棵独立子树，每棵各有一个 `robotN_map -> robotN_odom` 链。

单独验证某段变换：

```bash
ros2 run tf2_ros tf2_echo map robot1_base_link
ros2 run tf2_ros tf2_echo map robot2_base_link
```

---

## 十一、双机 SLAM 建图

### 原理

每台机器人独立运行 slam_toolbox，各自发布局部地图。
**关键**：两车的 `map_frame` 必须不同（`robot1_map` / `robot2_map`），
否则会同时往 `map -> robotN_odom` 发 TF，冲突。

### 启动 slam_toolbox（robot1）

```bash
source ~/multi-robot-avoidance-sim/multi-robot-avoidance-sim_ws/install/setup.bash

ros2 run slam_toolbox async_slam_toolbox_node \
  --ros-args \
  -r __ns:=/robot1 \
  -r /scan:=/robot1/scan \
  -r /map:=/robot1/map \
  -r /map_metadata:=/robot1/map_metadata \
  -r /map_updates:=/robot1/map_updates \
  -p use_sim_time:=true \
  -p odom_frame:=robot1_odom \
  -p base_frame:=robot1_base_link \
  -p map_frame:=robot1_map \
  -p minimum_travel_distance:=0.3 \
  -p minimum_travel_heading:=0.3 \
  -p max_laser_range:=8.0
```

### 启动 slam_toolbox（robot2）

```bash
source ~/multi-robot-avoidance-sim/multi-robot-avoidance-sim_ws/install/setup.bash

ros2 run slam_toolbox async_slam_toolbox_node \
  --ros-args \
  -r __ns:=/robot2 \
  -r /scan:=/robot2/scan \
  -r /map:=/robot2/map \
  -r /map_metadata:=/robot2/map_metadata \
  -r /map_updates:=/robot2/map_updates \
  -p use_sim_time:=true \
  -p odom_frame:=robot2_odom \
  -p base_frame:=robot2_base_link \
  -p map_frame:=robot2_map \
  -p minimum_travel_distance:=0.3 \
  -p minimum_travel_heading:=0.3 \
  -p max_laser_range:=8.0
```

### 建图要点

| 点 | 说明 |
|---|---|
| remap 左边必须带斜杠 | `-r /scan:=/robot1/scan`，不能写 `-r scan:=...` |
| `map_frame` 两车必须不同 | `robot1_map` / `robot2_map`，不能都是 `map` |
| 慢速移动 | 快速转弯会导致 scan 匹配错位，地图漂移 |
| 沿墙走 | 让激光扫到墙的轮廓，地图更准 |
| 一次 0.5~1 米 | 走一段停一下再走 |
| 两车建图时 | 分头跑，中间留重叠区域（为合并做准备） |

---

## 十二、RViz 查看地图

RViz 配置已内置在 `rviz/multi_robot.rviz`，启动 launch 时自动加载。

关键设置：

| 项目 | 值 |
|---|---|
| Fixed Frame | `map` |
| Map_robot1 Topic | `/robot1/map` |
| Map_robot2 Topic | `/robot2/map` |
| Map_merged Topic | `/map`（合并时才有） |
| Map Durability Policy | **Transient Local** ← 关键 |
| Map Reliability Policy | `Reliable` |
| Laser_robot1 Topic | `/robot1/scan`（绿） |
| Laser_robot2 Topic | `/robot2/scan`（红） |

> **注意**：RViz 默认 Durability 是 `Volatile`，与 slam_toolbox 的 `Transient Local` 不匹配，会显示 "No map received"。必须改成 `Transient Local`。

---

## 十三、保存地图

用 `nav2_map_server` 的 `map_saver_cli`，生成 Nav2 可直接用的 `pgm + yaml`。

**关键参数（必加）**：

- `-p map_subscribe_transient_local:=true` → 匹配 slam_toolbox 的 QoS
- `-p save_map_timeout:=10.0` → 避免默认 2 秒超时
- `-r /map:=/robotN/map` → 话题重映射

```bash
mkdir -p ~/multi-robot-avoidance-sim/multi-robot-avoidance-sim_ws/src/multi_robot_gazebo/maps

# 保存 robot1 地图
ros2 run nav2_map_server map_saver_cli \
  -f ~/multi-robot-avoidance-sim/multi-robot-avoidance-sim_ws/src/multi_robot_gazebo/maps/robot1_map \
  --ros-args \
  -p map_subscribe_transient_local:=true \
  -p save_map_timeout:=10.0 \
  -r /map:=/robot1/map

# 保存 robot2 地图
ros2 run nav2_map_server map_saver_cli \
  -f ~/multi-robot-avoidance-sim/multi-robot-avoidance-sim_ws/src/multi_robot_gazebo/maps/robot2_map \
  --ros-args \
  -p map_subscribe_transient_local:=true \
  -p save_map_timeout:=10.0 \
  -r /map:=/robot2/map
```

生成：

```text
maps/
├── robot1_map.pgm
├── robot1_map.yaml
├── robot2_map.pgm
└── robot2_map.yaml
```

> 保存时 slam_toolbox 必须**正在运行**，否则收不到地图。

---

## 十四、多机地图合并（实验性）

使用 `multirobot_map_merge` 尝试把两张局部地图合成一张全局地图。

### 安装

```bash
cd ~/multi-robot-avoidance-sim/multi-robot-avoidance-sim_ws/src
git clone https://ghproxy.net/https://github.com/robo-friends/m-explore-ros2.git
cd ..

rosdep install --from-paths src/m-explore-ros2 --ignore-src -r -y

# 关键：关掉测试，避免 cmake 下载 15MB 测试地图
colcon build --packages-select multirobot_map_merge --cmake-args -DBUILD_TESTING=OFF
source install/setup.bash
```

### 启动合并

```bash
ros2 launch multi_robot_gazebo map_merge.launch.py
```

合并后 `/map` 话题出现。RViz 里 `Map_merged` display 选 `/map` 查看。

### 已知问题

在当前 Gazebo 简单室内房间 + 差速小车 SLAM 场景下，**地图合并未能稳定成功**：

- 特征匹配模式：`matches` 长期个位数，`inliers` 2~3，`confidence` 0.2 左右，无法接受
- 已知初始位姿模式：两图各自按 `map` 原点摆放，未对齐

**原因**：

- 房间墙太平整，激光特征点少
- 两台车 SLAM 各自漂移，即使同一面墙，形状也有差异
- `multirobot_map_merge` 对内点率要求较高（通常 >60%）

**结论**：本仿真采用**双机独立建图**方案，两张局部地图分开保存、分开使用。
地图合并作为实验性功能保留。

### 若想尝试改进

- 在 `walls.world` 里加箱子、柱子、门框，增加可匹配特征
- 两车都走到房间中央，扫到同一片墙，重叠区域 >50%
- 建图时慢速走，减小 SLAM 漂移
- 或用 `robot_localization` 融合里程计

---

## 十五、添加第三台机器人

编辑 `launch/multi_robot.launch.py`，在 `ROBOTS` 列表加一行：

```python
ROBOTS = [
    {'name': 'robot1', 'x': '-1.5', 'y': '0.0',  'yaw': '0.0'},
    {'name': 'robot2', 'x': '1.5',  'y': '0.0',  'yaw': '3.14159'},
    {'name': 'robot3', 'x': '0.0',  'y': '1.5',  'yaw': '1.5708'},
]
```

重新编译。URDF 和插件会自动带上 `robot3` 前缀。

第三台车的 slam_toolbox 启动命令（把 robot2 全部替换成 robot3 即可）：

```bash
ros2 run slam_toolbox async_slam_toolbox_node \
  --ros-args \
  -r __ns:=/robot3 \
  -r /scan:=/robot3/scan \
  -r /map:=/robot3/map \
  -r /map_metadata:=/robot3/map_metadata \
  -r /map_updates:=/robot3/map_updates \
  -p use_sim_time:=true \
  -p odom_frame:=robot3_odom \
  -p base_frame:=robot3_base_link \
  -p map_frame:=robot3_map
```

---

## 十六、参数修改

| 参数 | 位置 | 说明 |
|---|---|---|
| 车体尺寸 | `urdf/diff_robot.urdf.xacro` | `<box size="0.4 0.3 0.15"/>` |
| 轮距 | `urdf/diff_robot.urdf.xacro` | `wheel_separation`（0.34） |
| 轮径 | `urdf/diff_robot.urdf.xacro` | `wheel_diameter`（0.12） |
| 雷达范围 | `urdf/diff_robot.urdf.xacro` | `<max>10.0</max>` |
| 雷达采样数 | `urdf/diff_robot.urdf.xacro` | `<samples>360</samples>` |
| 初始位置 | `launch/multi_robot.launch.py` | `ROBOTS` 列表的 `x`、`y`、`yaw` |
| 世界场景 | `launch/multi_robot.launch.py` | `'world': ...` 那一行 |

**注意**：`yaw` 必须写成**数值**（如 `3.14159`），不能写成字符串 `'{math.pi:.6f}'`，
否则 `static_transform_publisher` 和 `spawn_entity.py` 会报 `invalid float value`。

---

## 十七、常见问题

| 问题 | 原因 | 解决 |
|---|---|---|
| Gazebo 里车不动 | 仿真暂停 | 点一下 Gazebo 界面，按空格取消暂停 |
| 两车重叠 | spawn 位置相同 | 修改 `ROBOTS` 列表中的 `x`、`y` |
| TF 里没有 `map` 帧 | launch 里没发 `map -> robotN_map` | 确认 `spawn_robot` 里有 `static_transform_publisher` |
| RViz 显示 No map received | Durability Policy 不对 | Map display 的 Durability 改成 `Transient Local` |
| slam_toolbox 收不到 scan | remap 左边缺斜杠 | `-r /scan:=/robot1/scan`，不是 `-r scan:=...` |
| TF 冲突/乱跳 | 两车 `map_frame` 都用了 `map` | 改成 `robot1_map` / `robot2_map` |
| `Failed to parse --yaw` 或 `invalid float value` | `yaw` 写成了字符串 | 改成数值 |
| `map_saver_cli: Failed to spin map subscription` | QoS 不匹配 / 超时太短 | 加 `-p map_subscribe_transient_local:=true -p save_map_timeout:=10.0` |
| `map_saver_cli: Failed to write map` | maps 目录不存在 | `mkdir -p .../maps` 后重试 |
| slam_toolbox save_map result=255 | 地图为空 / 没建到图 | 先用 teleop 让车走一段再保存 |
| `multirobot_map_merge` 编译卡住 10 分钟 | cmake 在下测试地图 | 加 `--cmake-args -DBUILD_TESTING=OFF` |
| `multirobot_map_merge` install 目录消失 | 误删了 install | 重新 `colcon build --packages-select multirobot_map_merge` |
| git push 报 no upstream branch | git 分支没设上游 | `git push -u origin main` |
| git clone GitHub 失败 | 网络访问慢/被阻断 | 用镜像 `https://ghproxy.net/https://github.com/...` |

---

## 十八、下一步扩展

- [x] 双机独立 SLAM 建图
- [x] RViz 双地图显示
- [ ] Nav2 导航：每台车独立配置 nav2 参数，共享同一张地图
- [ ] 多机地图合并（multirobot_map_merge）：当前实验性，需加强环境特征
- [ ] 接入 UDP 协同避障：把 `multi_udp` 的调度逻辑接到仿真里
- [ ] 动态障碍物：加入移动障碍，测试避障算法
- [ ] 多机协同探索：多台车协同覆盖未知区域

---

## 十九、许可

MIT License

## 二十、作者

杨静