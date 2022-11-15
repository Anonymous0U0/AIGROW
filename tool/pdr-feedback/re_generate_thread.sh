read p1 p2 p3<params
python3 bin/GraFuzzer_nolimit.py --re-generate=1 --input-ratio=$p1 --latch-ratio=$p2 --and-ratio=$p3 --target-file="temp/gen$2.aag" --based-file=aigerfile_thread/$1
./bin/aigtoaig "temp/gen$2.aag" "temp/gen$2.aig"
timeout 2h ./bin/abc -c "pdr" "temp/gen$2.aig"
echo $?