pid=$(ps -ef | grep python3 | grep -v grep | awk '{print $2}')

for i in $pid
do
    kill $i
done
