#!/usr/bin/env bash
while [[ $# -gt 0 ]]; do
  key="$1"

  case $key in
  -file)
    FILE="$2"
    shift # past argument
    shift # past value
    ;;
  -blockchain)
    BLOCKCHAIN="$2"
    shift
    shift
    ;;
  -start)
    START="$2"
    shift # past argument
    shift # past value
    ;;
  -end)
    END="$2"
    shift
    shift
    ;;
  -api)
    API="$2"
    shift
    shift
    ;;
  -res)
    RES="$2"
    shift
    shift
    ;;
  -cores)
    CORES="$2"
    shift
    shift
    ;;
  esac
done

case $FILE in
eth | ethereum | Ethereum | ETH)
  python3 ethereum.py $API $START $END $RES $CORES
  ;;
  test)
  python3 test.py 
  ;;
xrp | ripple | Ripple | XRP)
  python3 ripple.py $START $END $RES $CORES
  ;;
sochain | doge | dogecoin | Dogecoin | DOGE | ltc | litecoin | Litecoin | LTC | btc | bitcoin | Bitcoin | BTC)
  python3 sochain.py $BLOCKCHAIN $START $END $RES $CORES
  ;;
*)
  echo "DLT not available. Allowed options are: -eth, -btc, -xrp, -sochain"
  ;;
esac




