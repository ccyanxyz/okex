function check(){
    count=`ps -ef | grep my_watcher | grep -v 'grep' | wc -l`
    
    if [ 0 == $count ];then
	python3 my_watcher.py
    fi
}

while true 
do
    check
done
