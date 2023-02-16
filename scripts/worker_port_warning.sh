# Warn if non-standard worker_api_port is being used, likely default value they did not override properly
if [[ "${blockchains}"  == "apple" && "${worker_api_port}" != '8947' ]]; then
  echo "Apple worker with non-standard worker_api_port of ${worker_api_port} found.  Did you mean to use 8947?"
fi
if [[ "${blockchains}"  == "ballcoin" && "${worker_api_port}" != '8597' ]]; then
  echo "Ballcoin worker with non-standard worker_api_port of ${worker_api_port} found.  Did you mean to use 8957?"
fi
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
if [[ "${blockchains}"  == "chinilla" && "${worker_api_port}" != '8948' ]]; then
  echo "Chinilla worker with non-standard worker_api_port of ${worker_api_port} found.  Did you mean to use 8948?"
fi
if [[ "${blockchains}"  == "chives" && "${worker_api_port}" != '8931' ]]; then
  echo "Chives worker with non-standard worker_api_port of ${worker_api_port} found.  Did you mean to use 8931?"
fi
if [[ "${blockchains}"  == "coffee" && "${worker_api_port}" != '8954' ]]; then
  echo "Coffee worker with non-standard worker_api_port of ${worker_api_port} found.  Did you mean to use 8954?"
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
if [[ "${blockchains}"  == "greenbtc" && "${worker_api_port}" != '8955' ]]; then
  echo "GreenBTC worker with non-standard worker_api_port of ${worker_api_port} found.  Did you mean to use 8955?"
fi
if [[ "${blockchains}"  == "gigahorse" && "${worker_api_port}" != '8959' ]]; then
  echo "Gigahorse worker with non-standard worker_api_port of ${worker_api_port} found.  Did you mean to use 8959?"
fi
if [[ "${blockchains}"  == "gold" && "${worker_api_port}" != '8949' ]]; then
  echo "Gold worker with non-standard worker_api_port of ${worker_api_port} found.  Did you mean to use 8949?"
fi
if [[ "${blockchains}"  == "hddcoin" && "${worker_api_port}" != '8930' ]]; then
  echo "HDDCoin worker with non-standard worker_api_port of ${worker_api_port} found.  Did you mean to use 8930?"
fi
if [[ "${blockchains}"  == "littlelambocoin" && "${worker_api_port}" != '8946' ]]; then
  echo "LittleLamboCoin worker with non-standard worker_api_port of ${worker_api_port} found.  Did you mean to use 8946?"
fi
if [[ "${blockchains}"  == "maize" && "${worker_api_port}" != '8933' ]]; then
  echo "Maize worker with non-standard worker_api_port of ${worker_api_port} found.  Did you mean to use 8933?"
fi
if [[ "${blockchains}"  == "mint" && "${worker_api_port}" != '8950' ]]; then
  echo "Mint worker with non-standard worker_api_port of ${worker_api_port} found.  Did you mean to use 8950?"
fi
if [[ "${blockchains}"  == "mmx" && "${worker_api_port}" != '8940' ]]; then
  echo "MMX worker with non-standard worker_api_port of ${worker_api_port} found.  Did you mean to use 8940?"
fi
if [[ "${blockchains}"  == "moon" && "${worker_api_port}" != '8953' ]]; then
  echo "Moon worker with non-standard worker_api_port of ${worker_api_port} found.  Did you mean to use 8953?"
fi
if [[ "${blockchains}"  == "nchain" && "${worker_api_port}" != '8929' ]]; then
  echo "N-Chain worker with non-standard worker_api_port of ${worker_api_port} found.  Did you mean to use 8936?"
fi 
if [[ "${blockchains}"  == "one" && "${worker_api_port}" != '8956' ]]; then
  echo "One blockchain worker with non-standard worker_api_port of ${worker_api_port} found.  Did you mean to use 8956?"
fi
if [[ "${blockchains}"  == "petroleum" && "${worker_api_port}" != '8943' ]]; then
  echo "Petroleum worker with non-standard worker_api_port of ${worker_api_port} found.  Did you mean to use 8943?"
fi
if [[ "${blockchains}"  == "pipscoin" && "${worker_api_port}" != '8958' ]]; then
  echo "Pipscoin worker with non-standard worker_api_port of ${worker_api_port} found.  Did you mean to use 8958?"
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
if [[ "${blockchains}"  == "tad" && "${worker_api_port}" != '8951' ]]; then
  echo "Tad worker with non-standard worker_api_port of ${worker_api_port} found.  Did you mean to use 8951?"
fi 
if [[ "${blockchains}"  == "wheat" && "${worker_api_port}" != '8952' ]]; then
  echo "Wheat worker with non-standard worker_api_port of ${worker_api_port} found.  Did you mean to use 8952?"
fi 