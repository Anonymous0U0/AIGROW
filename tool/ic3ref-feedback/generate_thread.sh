read p1 p2 p3<params
timeout 1m python3 bin/GraFuzzer_nolimit.py --re-generate=0 --input-ratio=$p1 --latch-ratio=$p2 --and-ratio=$p3 --target-file="temp/gen$1.aag"
echo $?
./bin/aigtoaig "temp/gen$1.aag" "temp/gen$1.aig"
