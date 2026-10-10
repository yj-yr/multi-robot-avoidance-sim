# Multi-Robot Collision Avoidance Simulation

两台机器人在共享二维平面内运动，通过预测未来轨迹提前检测冲突，依据优先级分配通行权，实现无碰撞协同导航。

纯 Python 仿真，不依赖 ROS2，clone 后即可运行。

## 效果

- 两台机器人从不同起点出发，走向各自目标
- 每 0.3 s 预测未来 3 s 轨迹
- 预测最小距离小于安全阈值 0.8 m 时，编号大的机器人停车让行
- 冲突解除后自动恢复

## 快速开始

    pip install -r requirements.txt
    python3 simulate.py

## 算法说明

### 轨迹预测

采用匀速直线模型，在每个预测步长内根据当前速度外推位置。

### 冲突检测

逐点比较两机预测轨迹，取最小欧氏距离作为预测最小距离。

### 优先级调度

编号小的机器人优先通行，编号大的停车让行。停车通过覆盖速度指令实现，恢复后由导航层重新接管。

## 参数

| 参数 | 默认值 | 说明 |
|---|---|---|
| T_PRED | 3.0 s | 预测时长 |
| PRED_DT | 0.3 s | 预测步长 |
| D_SAFE | 0.8 m | 安全距离阈值 |
| D_WARN | 1.5 m | 预警距离阈值 |
| V_NOM | 0.5 m/s | 标称速度 |

## 目录

    multi-robot-avoidance-sim/
    ├── README.md
    ├── LICENSE
    ├── requirements.txt
    └── simulate.py

## 许可

MIT License

## 作者

杨静
