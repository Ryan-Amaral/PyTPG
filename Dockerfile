FROM python:3.7

#Update & get sudo & cmake
#Need sudo for llvm install
#Need cmake for gym['atari'] install
RUN apt-get update && apt-get -y install sudo && apt-get -y install cmake 

WORKDIR /usr/src/app

#Copy tpg files
COPY . .

#Need to install llvm as pre-req for llvmlite python module 
RUN sudo apt-get -y install llvm

RUN pip install numpy
RUN pip install matplotlib
RUN pip install llvmlite
RUN pip install pathlib
RUN pip install msal
RUN pip install microsoftgraph-python 
RUN pip install requests
RUN pip install pandas
RUN pip install gym['atari']
RUN pip install -e .

CMD ["python", "run_mp.py", "Boxing-v0", "2000", "10", "18000", "12", "600", "true", "team", "./results/", "results", "ms_graph_config.json", "notify.json" ]
ENTRYPOINT [ "python", "run_mp.py"]
#python run_mp.py Boxing-v0 5 1 18000 12 5 true learner ./results/ results ms_graph_config.json notify.json

#sudo docker run --hostname alex-docker -d nimslab/tpg-v2:latest "Boxing-v0" 25 1 18000 40 600 true team "./alex25test/" alex_tpg_boxing_25 "conf.json" "notify.json"