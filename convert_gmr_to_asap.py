#!/usr/bin/env python3
import argparse
import os
import sys
import numpy as np
import joblib
from scipy.spatial.transform import Rotation as R
from omegaconf import OmegaConf

# 兼容某些由 numpy2 序列化、在 numpy1 环境反序列化时报 numpy._core 的情况
import numpy.core as npcore
sys.modules["numpy._core"] = npcore
sys.modules["numpy._core.multiarray"] = npcore.multiarray

from humanoidverse.utils.motion_lib.torch_humanoid_batch import Humanoid_Batch


def ensure_clip_dict(src):
    """
    支持两种输入：
    1) 平铺单条：{'fps','root_pos','root_rot','dof_pos',...}
    2) 多条字典：{'clipA': {...}, 'clipB': {...}}
    """
    if isinstance(src, dict) and {"fps", "root_pos", "root_rot", "dof_pos"}.issubset(src.keys()):
        return {"clip_000": src}
    return src


def quat_to_rotvec(root_quat, quat_order="xyzw"):
    root_quat = np.asarray(root_quat, dtype=np.float64)
    if quat_order == "wxyz":
        # wxyz -> xyzw
        root_quat = root_quat[:, [1, 2, 3, 0]]
    return R.from_quat(root_quat).as_rotvec().astype(np.float32), root_quat.astype(np.float32)


def convert_one_clip(clip, humanoid_fk, quat_order="xyzw"):
    required = ["fps", "root_pos", "root_rot", "dof_pos"]
    for k in required:
        if k not in clip:
            raise KeyError(f"缺少字段: {k}")

    fps = float(clip["fps"])
    root_pos = np.asarray(clip["root_pos"], dtype=np.float32)      # [T,3]
    root_rot = np.asarray(clip["root_rot"], dtype=np.float64)      # [T,4]
    dof_pos = np.asarray(clip["dof_pos"], dtype=np.float32)        # [T,D]

    if root_pos.ndim != 2 or root_pos.shape[1] != 3:
        raise ValueError(f"root_pos 形状应为 [T,3]，当前={root_pos.shape}")
    if root_rot.ndim != 2 or root_rot.shape[1] != 4:
        raise ValueError(f"root_rot 形状应为 [T,4]，当前={root_rot.shape}")
    if dof_pos.ndim != 2:
        raise ValueError(f"dof_pos 形状应为 [T,D]，当前={dof_pos.shape}")

    T = root_pos.shape[0]
    if root_rot.shape[0] != T or dof_pos.shape[0] != T:
        raise ValueError("时间长度不一致：root_pos/root_rot/dof_pos 的 T 必须相同")

    num_dof = humanoid_fk.num_dof
    if dof_pos.shape[1] != num_dof:
        raise ValueError(f"dof 维度不一致：数据 D={dof_pos.shape[1]}，配置 num_dof={num_dof}")

    num_aug = len(getattr(humanoid_fk.cfg, "extend_config", []))
    total_joints = 1 + num_dof + num_aug  # root + dof + augment

    # root quaternion -> axis-angle
    root_rotvec, root_quat_xyzw = quat_to_rotvec(root_rot, quat_order=quat_order)  # [T,3]

    # dof -> axis-angle: aa = axis * angle
    dof_axis = humanoid_fk.dof_axis.detach().cpu().numpy().astype(np.float32)  # [D,3]
    dof_aa = dof_pos[:, :, None] * dof_axis[None, :, :]                         # [T,D,3]

    # 组装 pose_aa: [T, J, 3]
    pose_aa = np.zeros((T, total_joints, 3), dtype=np.float32)
    pose_aa[:, 0, :] = root_rotvec
    pose_aa[:, 1:1 + num_dof, :] = dof_aa
    # augment joints 保持 0（若你配置了 extend_config，这里先按静止处理）

    out = {
        "root_trans_offset": root_pos,  # 对接 ASAP loader 关键字段
        "pose_aa": pose_aa,             # 对接 ASAP loader 关键字段
        "dof": dof_pos,                 # 可选，保留
        "root_rot": root_quat_xyzw,     # 可选，保留（xyzw）
        "fps": fps,
    }
    return out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="GMR 输出 pkl 路径")
    parser.add_argument("--output", required=True, help="ASAP 兼容 pkl 输出路径")
    parser.add_argument("--robot_cfg", required=True, help="机器人配置 yaml 路径")
    parser.add_argument("--quat_order", choices=["xyzw", "wxyz"], default="xyzw")
    args = parser.parse_args()

    if not os.path.exists(args.input):
        raise FileNotFoundError(args.input)
    if not os.path.exists(args.robot_cfg):
        raise FileNotFoundError(args.robot_cfg)

    cfg = OmegaConf.load(args.robot_cfg)
    humanoid_fk = Humanoid_Batch(cfg.robot.motion)

    src = joblib.load(args.input)
    clips = ensure_clip_dict(src)

    out = {}
    for name, clip in clips.items():
        if not isinstance(clip, dict):
            continue
        out[name] = convert_one_clip(clip, humanoid_fk, quat_order=args.quat_order)

    if len(out) == 0:
        raise RuntimeError("没有可转换的 clip，请检查输入 pkl 结构")

    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    joblib.dump(out, args.output)
    print(f"[OK] converted clips={len(out)} -> {args.output}")


if __name__ == "__main__":
    main()
