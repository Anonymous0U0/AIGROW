timeout 2h ./bin/IC3 -s < temp/gen$1.aig | tail -n 14
# ./IC3 -s < temp/gen$1.aig | tail -n 14
echo $?