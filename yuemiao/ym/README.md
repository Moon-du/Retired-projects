#### 项目结构

+ conf
    + account
    + logger
    + notification
    + proxy
    + region
+ core
    + listening
    + proxy_listening
    + auto_reservation
+ logs
+ README.md
+ requirements.txt
+ start.py

#### 运行环境：python3.10.0

1. 更新源安装依赖
    + `sudo apt-get update`
    + `sudo apt-get install libqgispython3.10.4`
    + `sudo apt-get install libpython3.10-stdlib`
2. 下载源码包  [python官方下载地址](https://www.python.org/downloads/source/)
    + `wget https://www.python.org/ftp/python/3.10.0/Python-3.10.0.tar.xz`
3. 解压源码
    + `tar -xvf Python-3.10.0.tgz`
4. 切换到源码目录
    + `cd Python-3.10.0/`
5. 设置编译参数，即输出文件目录
    + `./configure --prefix=/usr/local/python3`
6. 编译安装
    + `make && sudo make install`
7. 设置软连接
    + `cd /usr/bin`
    + `sudo rm ./python # 删除原有的软连接文件`
    + `sudo rm ./pip`
    + `sudo rm ./pip3`
    + `sudo ln -s /usr/local/python3/bin/python3.10 /usr/bin/python # 设置新的软连接`
    + `sudo ln -s /usr/local/python3/bin/pip3.10 /usr/bin/pip`
    + `sudo ln -s /usr/local/python3/bin/pip3.10 /usr/bin/pip3`
8. 检查python pip版本
    + `python3 --version && pip3 --version`
9. 安装依赖库
    + `sudo pip3 install -r requirements.txt`

#### 运行步骤

1. conf.account 设置账号 `cookie tk linkman_id`
2. conf.logger 设置日志输出路径
3. conf.region 设置监听区域
4. conf.proxy 监听两个以上地区需要设置代理相关信息
5. start 添加要监听的地区到线程池 运行`start.py`
    + 启动服务
   ```
    ps -ef | grep "python3 -u start.py" | grep -v grep | awk '{print $2}' | xargs kill -9
    cd /home/ym
    sudo nohup python3 -u start.py > ./logs/ym.log 2>&1 &
    echo "启动成功"
   ```
    + 停止服务
   ```
    ps -ef | grep "python3 -u start.py" | grep -v grep | awk '{print $2}' | xargs kill -9
    ps -ef | grep "python3 -u start.py" | grep -v grep 
   ```
    + 查看日志
   ```
   tail -f /home/ym/logs/ym.log
   tail -f /home/ym/logs/*.log
   ```

#### 后续迭代计划

+ 4.0版本开启自动预约
+ 5.0版本开发前端UI
+ ...
