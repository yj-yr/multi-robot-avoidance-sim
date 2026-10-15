# Multi-Robot Gazebo Simulation

基于 ROS2 Humble + Gazebo Classic 11 的双机器人命名空间仿真。

两台差速小车在同一室内房间中运行，各自拥有独立话题、TF 树和传感器，
通过命名空间隔离，可在 RViz 中同时可视化，并支持双机独立 SLAM 建图、
地图保存、地图合并（实验性）。

---

## 一、效果

- Gazebo 室内房间场景中生成两台差速小车
- robot1 与 robot2 各自独立命名空间
- 每台车带激光雷达、里程计、差速驱动插件
- 所有话题、TF 帧均在命名空间下，互不干扰
- RViz 同时显示两台车的模型、激光、地图
- 每台车独立运行 slam_toolbox 建图
- 地图保存为 Nav2 可用格式（pgm + yaml）
- 支持多机地图合并（实验性）

---

## 二、目录结构

```text
multi-robot-avoidance-sim_ws/
├── src/
│   ├── multi_robot_gazebo/
│   │   ├── package.xml
│   │   ├── CMakeLists.txt
│   │   ├── README.md
│   │   ├── launch/
│   │   │   ├── multi_robot.launch.py    # 启动 Gazebo + 两机 + RViz
│   │   │   └── map_merge.launch.py      # 多机地图合并
│   │   ├── urdf/
│   │   │   └── diff_robot.urdf.xacro    # 差速小车模型（支持前缀）
│   │   ├── worlds/
│   │   │   ├── empty.world
│   │   │   └── walls.world              # 室内房间场景
│   │   ├── rviz/
│   │   │   └── multi_robot.rviz         # 双机可视化配置
│   │   └── maps/                        # 保存的地图
│   │       ├── robot1_map.pgm / .yaml
│   │       ├── robot2_map.pgm / .yaml
│   │       └── merged_map.pgm / .yaml   # 合并结果（实验性）
│   └── m-explore-ros2/                  # 地图合并依赖
```

---

## 三、依赖安装

```bash
sudo apt install ros-humble-gazebo-ros-pkgs \
                 ros-humble-robot-state-publisher \
                 ros-humble-xacro \
                 ros-humble-rviz2 \
                 ros-humble-slam-toolbox \
                 ros-humble-teleop-twist-keyboard \
                 ros-humble-nav2-map-server
```

可选（地图合并）：

```bash
cd ~/multi-robot-avoidance-sim/multi-robot-avoidance-sim_ws/src
git clone https://ghproxy.net/https://github.com/robo-friends/m-explore-ros2.git
cd ..
rosdep install --from-paths src/m-explore-ros2 --ignore-src -r -y

# 关键：必须关测试，否则 cmake 会下载 15MB 测试地图，卡 10 分钟
colcon build --packages-select multirobot_map_merge --cmake-args -DBUILD_TESTING=OFF
```

---

## 四、编译

```bash
cd ~/multi-robot-avoidance-sim/multi-robot-avoidance-sim_ws
colcon build --symlink-install --packages-select multi_robot_gazebo
source install/setup.bash
```

> 用 `--symlink-install`，以后改 launch / rviz / urdf 不用重编。

**每个新终端都要先 source**：

```bash
source ~/multi-robot-avoidance-sim/multi-robot-avoidance-sim_ws/install/setup.bash
```

---

## 五、启动仿真

**终端 1**：

```bash
cd ~/multi-robot-avoidance-sim/multi-robot-avoidance-sim_ws
source install/setup.bash
ros2 launch multi_robot_gazebo multi_robot.launch.py
```

启动流程：

1. Gazebo 弹出场景
2. 2 秒后 spawn robot1 到 `(-1.5, 0)`，朝向 0°
3. 4 秒后 spawn robot2 到 `(1.5, 0)`，朝向 180°
4. 6 秒后启动 RViz

> Gazebo 里车不动？点一下 Gazebo 窗口，按空格取消暂停。

---

## 六、命名空间与 TF 结构

| 机器人 | 命名空间 | TF 帧前缀 | 初始位置 | 初始朝向 |
|---|---|---|---|---|
| robot1 | /robot1 | robot1_ | (-1.5, 0) | 0° |
| robot2 | /robot2 | robot2_ | (1.5, 0) | 180° |

### TF 树

```text
map                                    ← Gazebo 世界坐标（launch 里 static TF 发布）
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

**关键分层**：

| 变换 | 谁发 | 说明 |
|---|---|---|
| `map -> robotN_map` | launch 里 `static_transform_publisher` | 固定值 = Gazebo 初始位置 |
| `robotN_map -> robotN_odom` | slam_toolbox | 动态，会漂移 |
| `robotN_odom -> robotN_base_link` | Gazebo diff_drive 插件 | 里程计 |

**注意**：不要在 launch 里用 `static_transform_publisher` 发 `map -> robotN_odom`，会和 slam_toolbox 冲突。

### 验证 TF

```bash
ros2 run tf2_tools view_frames
evince frames.pdf

ros2 run tf2_ros tf2_echo map robot1_base_link
ros2 run tf2_ros tf2_echo map robot2_base_link
```

---

## 七、话题列表

```bash
ros2 topic list | grep robot
```

预期：

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

## 八、速度控制

### 方式一：键盘控制（teleop）

**控制 robot1（终端 A）**：

```bash
source ~/multi-robot-avoidance-sim/multi-robot-avoidance-sim_ws/install/setup.bash

ros2 run teleop_twist_keyboard teleop_twist_keyboard \
  --ros-args -r /cmd_vel:=/robot1/cmd_vel
```

**控制 robot2（终端 B）**：

```bash
source ~/multi-robot-avoidance-sim/multi-robot-avoidance-sim_ws/install/setup.bash

ros2 run teleop_twist_keyboard teleop_twist_keyboard \
  --ros-args -r /cmd_vel:=/robot2/cmd_vel
```

按键：`i` 前进，`j` 左转，`l` 右转，`,` 后退，`k` 停。

### 方式二：直接发速度指令

```bash
# robot1 前进（持续发 10Hz）
ros2 topic pub /robot1/cmd_vel geometry_msgs/msg/Twist \
  "{linear: {x: 0.3}, angular: {z: 0.0}}" -r 10

# robot2 原地转圈
ros2 topic pub /robot2/cmd_vel geometry_msgs/msg/Twist \
  "{linear: {x: 0.0}, angular: {z: 0.5}}" -r 10
```

**发一次就走一小段**：

```bash
ros2 topic pub /robot1/cmd_vel geometry_msgs/msg/Twist \
  "{linear: {x: 0.3}, angular: {z: 0.0}}" --once
```

**停车**：

```bash
ros2 topic pub /robot1/cmd_vel geometry_msgs/msg/Twist \
  "{linear: {x: 0.0}, angular: {z: 0.0}}" --once
```

---

## 九、双机 SLAM 建图

### 原理

每台机器人独立运行 slam_toolbox，各自发布局部地图。

**关键**：两车的 `map_frame` 必须不同（`robot1_map` / `robot2_map`），
否则会同时往 `map -> robotN_odom` 发 TF，冲突。

### 启动 slam_toolbox（robot1，终端 C）

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

### 启动 slam_toolbox（robot2，终端 D）

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

### 建图操作

1. 用 teleop（第八节）控制两车走遍房间
2. **慢速**走，一次 0.5~1 米，转弯别快
3. 沿墙走一圈 + 中间横穿，覆盖整个房间
4. 两车尽量扫到同一片区域（为合并做准备）

### 关键点

| 点 | 说明 |
|---|---|
| remap 左边必须带斜杠 | `-r /scan:=/robot1/scan`，不能写 `-r scan:=...` |
| `map_frame` 两车必须不同 | `robot1_map` / `robot2_map` |
| 慢速移动 | 快速转弯会导致 scan 匹配错位 |
| 沿墙走 | 让激光扫到墙的轮廓，地图更准 |

---

## 十、RViz 查看地图

RViz 配置已内置在 `rviz/multi_robot.rviz`，启动 launch 时自动加载。

关键设置：

| 项目 | 值 |
|---|---|
| Fixed Frame | `map` |
| Map_robot1 Topic | `/robot1/map` |
| Map_robot2 Topic | `/robot2/map` |
| Map_merged Topic | `/map`（合并时才有） |
| **Map Durability Policy** | **`Transient Local`** ← 关键 |
| Map Reliability Policy | `Reliable` |
| Laser_robot1 Topic | `/robot1/scan`（绿） |
| Laser_robot2 Topic | `/robot2/scan`（红） |

> **注意**：RViz 默认 Durability 是 `Volatile`，与 slam_toolbox 的 `Transient Local` 不匹配，会显示 "No map received"。必须改成 `Transient Local`。

---

## 十一、保存地图

用 `nav2_map_server` 的 `map_saver_cli`，生成 Nav2 可直接用的 `pgm + yaml`。

### 关键参数（必加）

- `-p map_subscribe_transient_local:=true` → 匹配 slam_toolbox 的 QoS
- `-p save_map_timeout:=10.0` → 避免默认 2 秒超时
- `-r /map:=/robotN/map` → 话题重映射

### 保存 robot1 地图（终端 E）

```bash
source ~/multi-robot-avoidance-sim/multi-robot-avoidance-sim_ws/install/setup.bash

mkdir -p ~/multi-robot-avoidance-sim/multi-robot-avoidance-sim_ws/src/multi_robot_gazebo/maps

ros2 run nav2_map_server map_saver_cli \
  -f ~/multi-robot-avoidance-sim/multi-robot-avoidance-sim_ws/src/multi_robot_gazebo/maps/robot1_map \
  --ros-args \
  -p map_subscribe_transient_local:=true \
  -p save_map_timeout:=10.0 \
  -r /map:=/robot1/map
```

### 保存 robot2 地图

```bash
ros2 run nav2_map_server map_saver_cli \
  -f ~/multi-robot-avoidance-sim/multi-robot-avoidance-sim_ws/src/multi_robot_gazebo/maps/robot2_map \
  --ros-args \
  -p map_subscribe_transient_local:=true \
  -p save_map_timeout:=10.0 \
  -r /map:=/robot2/map
```

### 成功标志

```text
[INFO] [map_io]: Received a XXX X YYY map @ 0.05 m/pix
[INFO] [map_io]: Writing map occupancy data to .../robot1_map.pgm
[INFO] [map_io]: Writing map metadata to .../robot1_map.yaml
[INFO] [map_saver]: Map saved successfully
```

生成：

```text
maps/
├── robot1_map.pgm / .yaml
└── robot2_map.pgm / .yaml
```

> 保存时 slam_toolbox 必须**正在运行**，否则收不到地图。

---

## 十二、多机地图合并（实验性）

### 原理

`multirobot_map_merge` 订阅 `/robot1/map` 和 `/robot2/map`，
尝试对齐两张局部地图，合成一张全局 `/map`。

**前提**：两车地图必须有**重叠区域**（都扫过同一片墙）。

### 启动合并（终端 F）

```bash
source ~/multi-robot-avoidance-sim/multi-robot-avoidance-sim_ws/install/setup.bash
ros2 launch multi_robot_gazebo map_merge.launch.py
```

### 期望输出

```text
[map_merge]: Map merging started.
[map_merge]: Robot discovery started.
[map_merge]: adding robot [/robot1] to system
[map_merge]: adding robot [/robot2] to system
[map_merge]: Published merged map
```

### 验证合并成功

```bash
ros2 topic list | grep -w /map
ros2 topic hz /map
ros2 topic echo /map --once | head -30
```

- `/map` 出现
- 有频率（约 5Hz）
- `width`、`height` 不是 0

### 保存合并地图

```bash
ros2 run nav2_map_server map_saver_cli \
  -f ~/multi-robot-avoidance-sim/multi-robot-avoidance-sim_ws/src/multi_robot_gazebo/maps/merged_map \
  --ros-args \
  -p map_subscribe_transient_local:=true \
  -p save_map_timeout:=10.0 \
  -r /map:=/map
```

### 已知问题

在当前 Gazebo 简单室内房间 + 差速小车 SLAM 场景下，**地图合并未能稳定成功**：

- 特征匹配模式：`matches` 长期个位数，`inliers` 2~3，`confidence` 0.2 左右
- 已知初始位姿模式：两图各自按 `map` 原点摆放，未对齐

**原因**：

- 房间墙太平整，激光特征点少
- 两台车 SLAM 各自漂移
- `multirobot_map_merge` 对内点率要求较高

**结论**：本仿真采用**双机独立建图**方案，两张局部地图分开使用。
地图合并作为实验性功能保留。

### 若想尝试改进

- 在 `walls.world` 里加箱子、柱子、门框，增加可匹配特征
- 两车都走到房间中央，扫到同一片墙，重叠区域 >50%
- 建图时慢速走，减小 SLAM 漂移

---

## 十三、完整启动流程

按顺序，每个终端都先 `source`。

| 终端 | 内容 |
|---|---|
| 1 | `ros2 launch multi_robot_gazebo multi_robot.launch.py` |
| 2 | robot1 slam（第九节命令） |
| 3 | robot2 slam（第九节命令） |
| 4 | robot1 teleop（第八节命令） |
| 5 | robot2 teleop（第八节命令） |
| 6 | 建完图后保存地图（第十一节命令） |
| 7 | （可选）`ros2 launch multi_robot_gazebo map_merge.launch.py` |

### 一键启动仿真 + slam 的脚本（可选）

新建 `~/start_all.sh`：

```bash
#!/bin/bash
WS=~/multi-robot-avoidance-sim/multi-robot-avoidance-sim_ws
source $WS/install/setup.bash

# 启动仿真（后台）
ros2 launch multi_robot_gazebo multi_robot.launch.py &
sleep 8

# 启动两个 slam（后台）
ros2 run slam_toolbox async_slam_toolbox_node --ros-args \
  -r __ns:=/robot1 -r /scan:=/robot1/scan -r /map:=/robot1/map \
  -r /map_metadata:=/robot1/map_metadata -r /map_updates:=/robot1/map_updates \
  -p use_sim_time:=true -p odom_frame:=robot1_odom \
  -p base_frame:=robot1_base_link -p map_frame:=robot1_map &

ros2 run slam_toolbox async_slam_toolbox_node --ros-args \
  -r __ns:=/robot2 -r /scan:=/robot2/scan -r /map:=/robot2/map \
  -r /map_metadata:=/robot2/map_metadata -r /map_updates:=/robot2/map_updates \
  -p use_sim_time:=true -p odom_frame:=robot2_odom \
  -p base_frame:=robot2_base_link -p map_frame:=robot2_map &

wait
```

```bash
chmod +x ~/start_all.sh
~/start_all.sh
```

---

## 十四、参数修改

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

## 十五、上传 GitHub

### 首次上传

```bash
cd ~/multi-robot-avoidance-sim

# 生成 .gitignore（如果还没）
cat > .gitignore << 'EOF'
__pycache__/
*.py[cod]
.vscode/
.idea/
build/
install/
log/
*.bag
*.db3
.env
EOF

git init
git branch -M main
git config user.name "Jing Yang"
git config user.email "2590135656@qq.com"
git add .
git commit -m "init: ROS2 Humble 双机仿真与建图"
git remote add origin git@github.com:yj-yr/multi-robot-avoidance-sim.git
git push -u origin main
```

### 以后更新

```bash
cd ~/multi-robot-avoidance-sim
git add .
git commit -m "修改说明"
git push
```

### 如果 push 被拒

```bash
# 远程有本地没有的提交
git pull --rebase origin main
git push

# 或强制覆盖（个人项目、确认远程内容不重要时）
git push --force origin main
```

### 如果 SSH 报错

```bash
# 测试 SSH
ssh -T git@github.com
# 应输出 Hi yj-yr! You've successfully authenticated

# 没有 SSH key 就生成
ssh-keygen -t ed25519 -C "2590135656@qq.com"
cat ~/.ssh/id_ed25519.pub
# 把公钥贴到 https://github.com/settings/keys
```

---

## 十六、常见问题

| 问题 | 原因 | 解决 |
|---|---|---|
| Gazebo 里车不动 | 仿真暂停 | 点一下 Gazebo 界面，按空格取消暂停 |
| 两车重叠 | spawn 位置相同 | 修改 `ROBOTS` 列表中的 `x`、`y` |
| TF 里没有 `map` 帧 | launch 里没发 `map -> robotN_map` | 确认 `spawn_robot` 里有 `static_transform_publisher` |
| RViz 显示 No map received | Durability Policy 不对 | Map display 的 Durability 改成 `Transient Local` |
| slam_toolbox 收不到 scan | remap 左边缺斜杠 | `-r /scan:=/robot1/scan`，不是 `-r scan:=...` |
| TF 冲突/乱跳 | 两车 `map_frame` 都用了 `map` | 改成 `robot1_map` / `robot2_map` |
| `Failed to parse --yaw` | `yaw` 写成字符串 | 改成数值 |
| `map_saver_cli: Failed to spin map subscription` | QoS 不匹配 / 超时太短 | 加 `-p map_subscribe_transient_local:=true -p save_map_timeout:=10.0` |
| `map_saver_cli: Failed to write map` | maps 目录不存在 | `mkdir -p .../maps` 后重试 |
| `multirobot_map_merge` 编译卡住 10 分钟 | cmake 在下测试地图 | 加 `--cmake-args -DBUILD_TESTING=OFF` |
| `multirobot_map_merge` install 目录消失 | 误删了 install | 重新 `colcon build --packages-select multirobot_map_merge` |
| git 提示"嵌入式 git 仓库" | 子目录有独立 `.git` | `find . -name ".git" -type d` 找出并 `rm -rf` 多余的 |
| `Could not resolve host: github.com` | 网络/DNS 问题 | 换镜像或配置 DNS |
| `git push` 报 `fetch first` | 远程有本地没有的提交 | `git pull --rebase origin main` 或 `git push --force` |

---

## 十七、下一步扩展

- [x] 双机独立 SLAM 建图
- [x] RViz 双地图显示
- [x] 地图保存为 Nav2 格式
- [x] 上传 GitHub
- [ ] 多机地图合并（当前实验性，需加强环境特征）
- [ ] Nav2 导航：每台车独立配置 nav2 参数
- [ ] 接入 UDP 协同避障
- [ ] 动态障碍物：加入移动障碍，测试避障算法

---

## 十八、许可

MIT License

## 十九、作者

杨静