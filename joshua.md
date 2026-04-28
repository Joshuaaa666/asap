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


### 
git reset --hard HEAD
git clean -fd


git pull origin main

cd ~/projects/ASAP-main
git fetch origin
git reset --hard origin/main
git clean -fd
git status
