docker build -t asap . --network host \
  --build-arg HTTP_PROXY=http://127.0.0.1:7897 \
  --build-arg HTTPS_PROXY=http://127.0.0.1:7897

xhost +local:docker

docker run --gpus all -it --rm \
    --network=host \
    --env="DISPLAY=$DISPLAY" \
    --volume="/tmp/.X11-unix:/tmp/.X11-unix:rw" \
    --volume="$HOME/.Xauthority:/root/.Xauthority:rw" \
    --volume="$(pwd):/workspace/ASAP-main" \
    asap
# 进入容器后执行
cd /workspace/ASAP-main
source /opt/conda/etc/profile.d/conda.sh
conda activate hvgym
#   fit_smpl_shape.py(形状拟合)   产出humanoidverse/data/shape/.../shape_optimized_v1.pkl）
HYDRA_FULL_ERROR=1 python scripts/data_process/fit_smpl_shape.py +robot=SV1/sv1_v1_0_0
#     motion fitting：(动作拟合/重定向)   生成最终的 .pkl 动作文件
HYDRA_FULL_ERROR=1 python scripts/data_process/fit_smpl_motion.py +robot=SV1/sv1_v1_0_0

#     训练
HYDRA_FULL_ERROR=1 python humanoidverse/train_agent.py \
+simulator=isaacgym \
+exp=motion_tracking \
+domain_rand=NO_domain_rand \
+rewards=motion_tracking/reward_motion_tracking_dm_2real \
+robot=SV1/sv1_v1_0_0 \
+terrain=terrain_locomotion_plane \
+obs=motion_tracking/deepmimic_a2c_nolinvel_LARGEnoise_history \
num_envs=4090 \
project_name=SV1_Test \
experiment_name=SV1_MotionTrack \
robot.motion.motion_file="humanoidverse/data/motions/sv1_v1_0_0/TairanTestbed/singles/0-motions_raw_tairantestbed_smpl_video_CR7_level1_filter_amass.pkl" \
robot.policy_obs_dim=-1 \
robot.critic_obs_dim=-1 \
headless=true \
robot.asset.self_collisions=True



### 
git reset --hard HEAD
git clean -fd


git pull origin main

cd ~/projects/ASAP-main
git fetch origin
git reset --hard origin/main
git clean -fd
git status
