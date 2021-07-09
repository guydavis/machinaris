echo 'Configuring Flaxdog...'
mkdir -p /root/.chia/flaxdog/logs
cp -n /machinaris/config/flaxdog.sample.yaml /root/.chia/flaxdog/config.yaml
cp -f /machinaris/scripts/flaxdog_notifier.sh /root/.chia/flaxdog/notifier.sh && chmod 755 /root/.chia/flaxdog/notifier.sh

echo 'Starting Flaxdog...'
cd /flaxdog
# Existing flaxdogs are killed in chiadog_launch.sh
/flax-blockchain/venv/bin/python3 -u main.py --config /root/.chia/flaxdog/config.yaml > /root/.chia/flaxdog/logs/flaxdog.log 2>&1 &
