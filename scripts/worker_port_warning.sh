# Warn if non-standard worker_api_port is being used, likely default value they did not override properly
if [[ "${blockchains}"  == "bpx" && "${worker_api_port}" != '8945' ]]; then
  echo "BPX worker with non-standard worker_api_port of ${worker_api_port} found.  Did you mean to use 8945?"
fi
if [[ "${blockchains}"  == "btcgreen" && "${worker_api_port}" != '8938' ]]; then
  echo "BTCGreen worker with non-standard worker_api_port of ${worker_api_port} found.  Did you mean to use 8938?"
fi
if [[ "${blockchains}"  == "cactus" && "${worker_api_port}" != '8936' ]]; then
  echo "Cactus worker with non-standard worker_api_port of ${worker_api_port} found.  Did you mean to use 8936?"
fi
if [[ "${blockchains}"  == "chia" && "${worker_api_port}" != '8927' ]]; then
  echo "Chia worker with non-standard worker_api_port of ${worker_api_port} found.  Did you mean to use 8927?"
fi
if [[ "${blockchains}"  == "chives" && "${worker_api_port}" != '8931' ]]; then
  echo "Chives worker with non-standard worker_api_port of ${worker_api_port} found.  Did you mean to use 8931?"
fi
if [[ "${blockchains}"  == "cryptodoge" && "${worker_api_port}" != '8937' ]]; then
  echo "Cryptodoge worker with non-standard worker_api_port of ${worker_api_port} found.  Did you mean to use 8937?"
fi
if [[ "${blockchains}"  == "ecostake" && "${worker_api_port}" != '8942' ]]; then
  echo "Ecostake worker with non-standard worker_api_port of ${worker_api_port} found.  Did you mean to use 8942?"
fi
if [[ "${blockchains}"  == "flax" && "${worker_api_port}" != '8928' ]]; then
  echo "Flax worker with non-standard worker_api_port of ${worker_api_port} found.  Did you mean to use 8928?"
fi
if [[ "${blockchains}"  == "flora" && "${worker_api_port}" != '8932' ]]; then
  echo "Flora worker with non-standard worker_api_port of ${worker_api_port} found.  Did you mean to use 8932?"
fi
if [[ "${blockchains}"  == "hddcoin" && "${worker_api_port}" != '8930' ]]; then
  echo "HDDCoin worker with non-standard worker_api_port of ${worker_api_port} found.  Did you mean to use 8930?"
fi
if [[ "${blockchains}"  == "maize" && "${worker_api_port}" != '8933' ]]; then
  echo "Maize worker with non-standard worker_api_port of ${worker_api_port} found.  Did you mean to use 8933?"
fi
if [[ "${blockchains}"  == "mmx" && "${worker_api_port}" != '8940' ]]; then
  echo "Maize worker with non-standard worker_api_port of ${worker_api_port} found.  Did you mean to use 8940?"
fi
if [[ "${blockchains}"  == "nchain" && "${worker_api_port}" != '8929' ]]; then
  echo "N-Chain worker with non-standard worker_api_port of ${worker_api_port} found.  Did you mean to use 8936?"
fi 
if [[ "${blockchains}"  == "petroleum" && "${worker_api_port}" != '8943' ]]; then
  echo "Petroleum worker with non-standard worker_api_port of ${worker_api_port} found.  Did you mean to use 8943?"
fi
if [[ "${blockchains}"  == "profit" && "${worker_api_port}" != '8944' ]]; then
  echo "Profit worker with non-standard worker_api_port of ${worker_api_port} found.  Did you mean to use 8944?"
fi  
if [[ "${blockchains}"  == "shibgreen" && "${worker_api_port}" != '8939' ]]; then
  echo "Shibgreen worker with non-standard worker_api_port of ${worker_api_port} found.  Did you mean to use 8939?"
fi
if [[ "${blockchains}"  == "silicoin" && "${worker_api_port}" != '8941' ]]; then
  echo "Silicoin worker with non-standard worker_api_port of ${worker_api_port} found.  Did you mean to use 8941?"
fi
if [[ "${blockchains}"  == "staicoin" && "${worker_api_port}" != '8934' ]]; then
  echo "Staicoin worker with non-standard worker_api_port of ${worker_api_port} found.  Did you mean to use 8934?"
fi
if [[ "${blockchains}"  == "stor" && "${worker_api_port}" != '8935' ]]; then
  echo "Stor worker with non-standard worker_api_port of ${worker_api_port} found.  Did you mean to use 8935?"
fi 