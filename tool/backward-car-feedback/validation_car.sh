# timeout 2h ./simplecar -f -dead -propagate -muc -e "temp/gen$1.aig" temp
# echo $?
timeout 2h ./bin/simplecar -b -e "temp/gen$1.aig" temp
# 不设置超时
# ./simplecar -b -e "temp/gen$1.aig" temp
echo $?