#!/usr/bin/env python3
"""
多机器人协同避障仿真
--------------------------------------------------
两台机器人沿路径运动，每 0.3s 预测未来 3s 轨迹，
预测最小距离小于安全阈值时，编号大的机器人停车让行。

作者：杨静
"""
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.patches import Circle
from collections import deque

# ===== 参数 =====
DT = 0.05            # 仿真步长（秒）
T_PRED = 3.0         # 预测时长（秒）
PRED_DT = 0.3        # 预测步长（秒）
K = int(T_PRED / PRED_DT)
D_SAFE = 0.8         # 安全距离（米）
D_WARN = 1.5         # 预警距离（米）
V_NOM = 0.5          # 标称速度（米/秒）


class Robot:
    def __init__(self, rid, start, goal, color):
        self.rid = rid
        self.pos = np.array(start, dtype=float)
        self.goal = np.array(goal, dtype=float)
        self.color = color
        self.v = 0.0
        self.waiting = False
        self.trail = deque(maxlen=300)

    def step(self, dt):
        if self.waiting:
            self.v = 0.0
        else:
            d = np.linalg.norm(self.goal - self.pos)
            if d < 0.05:
                self.v = 0.0
            else:
                self.v = min(V_NOM, d / dt * 0.4)
                direction = (self.goal - self.pos) / d
                self.pos = self.pos + direction * self.v * dt
        self.trail.append(self.pos.copy())

    def predict(self):
        d = np.linalg.norm(self.goal - self.pos)
        if self.v < 1e-3 or d < 1e-6:
            return [self.pos.copy() for _ in range(K)]
        direction = (self.goal - self.pos) / d
        traj = []
        for k in range(1, K + 1):
            t = k * PRED_DT
            p = self.pos + direction * self.v * t
            if np.linalg.norm(p - self.pos) > d:
                p = self.goal.copy()
            traj.append(p)
        return traj


def min_predicted_distance(a, b):
    ta = a.predict()
    tb = b.predict()
    return min(np.linalg.norm(pa - pb) for pa, pb in zip(ta, tb))


def main():
    r1 = Robot(1, (0, 0), (5, 5), 'tab:blue')
    r2 = Robot(2, (5, 0), (0, 5), 'tab:orange')
    robots = [r1, r2]

    fig, ax = plt.subplots(figsize=(7, 7))
    ax.set_xlim(-1, 6)
    ax.set_ylim(-1, 6)
    ax.set_aspect('equal')
    ax.grid(True, alpha=0.3)
    ax.set_title('Multi-Robot Collision Avoidance Simulation')

    for r in robots:
        ax.plot(*r.goal, marker='*', color=r.color, markersize=15)

    safe_circles = [Circle(r.pos, D_SAFE, fill=False, ls='--',
                           color=r.color, alpha=0.5) for r in robots]
    warn_circles = [Circle(r.pos, D_WARN, fill=False, ls=':',
                           color=r.color, alpha=0.3) for r in robots]
    for c in safe_circles + warn_circles:
        ax.add_patch(c)

    trails = [ax.plot([], [], '-', color=r.color, lw=1.5, alpha=0.6)[0]
              for r in robots]
    preds = [ax.plot([], [], '--', color=r.color, lw=1, alpha=0.4)[0]
             for r in robots]
    dots = [ax.plot([], [], 'o', color=r.color, markersize=10)[0]
            for r in robots]

    info = ax.text(0.02, 0.98, '', transform=ax.transAxes,
                   va='top', fontsize=10, family='monospace')

    def update(_):
        d_min = min_predicted_distance(r1, r2)
        r2.waiting = d_min < D_SAFE

        for r in robots:
            r.step(DT)

        for i, r in enumerate(robots):
            trail = np.array(r.trail)
            if len(trail) > 0:
                trails[i].set_data(trail[:, 0], trail[:, 1])
            pp = np.array(r.predict())
            preds[i].set_data(pp[:, 0], pp[:, 1])
            dots[i].set_data([r.pos[0]], [r.pos[1]])
            safe_circles[i].center = r.pos
            warn_circles[i].center = r.pos

        status = 'WAIT' if r2.waiting else 'GO'
        info.set_text(
            f"predicted min distance : {d_min:.2f} m\n"
            f"safe threshold         : {D_SAFE:.2f} m\n"
            f"robot 1 (id=1)         : GO\n"
            f"robot 2 (id=2)         : {status}"
        )
        return trails + preds + dots + safe_circles + warn_circles + [info]

    anim = FuncAnimation(fig, update, frames=600,
                         interval=50, blit=False, repeat=False)
    plt.show()


if __name__ == '__main__':
    main()
