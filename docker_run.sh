docker run --rm -it \
  --env-file .env \
  --device /dev/snd \
  -v $(pwd)/source:/app/source \
  --group-add audio \
  -v /etc/machine-id:/etc/machine-id:ro \
  -v /run/user/$(id -u)/pulse:/run/user/$(id -u)/pulse \
  -v ~/.config/pulse/cookie:/home/$(whoami)/.config/pulse/cookie \
  -e PULSE_SERVER=unix:/run/user/$(id -u)/pulse/native \
  -u $(id -u):$(id -g) \
  achilles_image
