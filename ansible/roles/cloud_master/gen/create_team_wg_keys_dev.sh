#!/bin/bash

#NUM="$1"

CLTCOUNT=10

cd "$(dirname "${BASH_SOURCE[0]}")"

if [ -d net_keys_wg_dev ]; then
 echo "Remove net_keys_wg_dev first"
 exit 1
fi

mkdir net_keys_wg_dev
cd net_keys_wg_dev || exit 1


gen_conf() {
  NUM="$1"
  SRV_PRIV_KEY="$(wg genkey)"
  SRV_PUB_KEY="$(echo "$SRV_PRIV_KEY" | wg pubkey)"


  echo "$SRV_PRIV_KEY" > ${NUM}.srv.privkey.txt
  echo "$SRV_PUB_KEY" > ${NUM}.srv.pubkey.txt

  for c in `seq 1 ${CLTCOUNT}`; do
    CLT_PRIV_KEY="$(wg genkey)"
    CLT_PUB_KEY="$(echo "$CLT_PRIV_KEY" | wg pubkey)"
    echo "$CLT_PRIV_KEY" > ${NUM}.clt${c}.privkey.txt
    echo "$CLT_PUB_KEY" > ${NUM}.clt${c}.pubkey.txt
  done

}

for i in {1..64}; do
 gen_conf "$i"
done
