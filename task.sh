echo ======== start ========
echo date: $(date "+%Y-%m-%d %H:%M")
path=$(cd `dirname $0`; pwd)
cd /root/blog/flask
cd markdown
local_revision=`svn info --password 123 | grep "Last Changed Rev:" | awk '{print $4}'`
echo "the revision is $local_revision"
url=`svn info --password 123 | grep URL: | awk '{print $2}'`
remote_revision=`svn info $url --password 123 | grep "Last Changed Rev:" | awk '{print $4}'`
echo "the revision in svn is $remote_revision"
if [[ $local_revision < $remote_revision ]] ; then
    echo "need svn update"
    svn update --password 123
    echo "svn update finish"
    cd ..
    bash task.sh
    echo "make thumbnail finish"
else
    echo "not need svn update"
fi
cd $path
echo ========= end =========