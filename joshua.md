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
# 转换    || wxyz

python /tmp/convert_gmr_to_asap.py \
  --input humanoidverse/data/motions/SR1_V1.0.0/sr1_v1_test.pkl \
  --output humanoidverse/data/motions/SR1_V1.0.0/sr1_v1_test_asap.pkl \
  --robot_cfg humanoidverse/config/robot/SV1/sv1_v1.0.0.yaml \
  --quat_order xyzw

# test locomotion
HYDRA_FULL_ERROR=1 python humanoidverse/train_agent.py \
+simulator=isaacgym \
+exp=locomotion \
+domain_rand=NO_domain_rand \
+rewards=loco/reward_g1_locomotion \
+robot=g1/g1_29dof_anneal_23dof \
+terrain=terrain_locomotion_plane \
+obs=loco/leggedloco_obs_singlestep_withlinvel \
num_envs=2048 \
project_name=TestIsaacGymInstallation \
experiment_name=G123dof_loco \
headless=ture

# test manipulation
python humanoidverse/train_agent.py \
+simulator=isaacgym \
+exp=motion_tracking \
+domain_rand=NO_domain_rand \
+rewards=motion_tracking/reward_motion_tracking_dm_2real \
+robot=g1/g1_29dof_anneal_23dof \
+terrain=terrain_locomotion_plane \
+obs=motion_tracking/deepmimic_a2c_nolinvel_LARGEnoise_history \
num_envs=4096 \
project_name=MotionTracking \
experiment_name=MotionTracking_CR7 \
robot.motion.motion_file="humanoidverse/data/motions/g1_29dof_anneal_23dof/TairanTestbed/singles/0-TairanTestbed_TairanTestbed_CR7_video_CR7_level1_filter_amass.pkl" \
rewards.reward_penalty_curriculum=True \
rewards.reward_penalty_degree=0.00001 \
env.config.resample_motion_when_training=False \
env.config.termination.terminate_when_motion_far=True \
env.config.termination_curriculum.terminate_when_motion_far_curriculum=True \
env.config.termination_curriculum.terminate_when_motion_far_threshold_min=0.3 \
env.config.termination_curriculum.terminate_when_motion_far_curriculum_degree=0.000025 \
robot.asset.self_collisions=0

## visualize the policy 

python humanoidverse/eval_agent.py \
+checkpoint=logs/MotionTracking/xxxxxxxx_xxxxxxx-MotionTracking_CR7-motion_tracking-g1_29dof_anneal_23dof/model_5800.pt


