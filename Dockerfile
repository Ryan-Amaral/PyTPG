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
RUN pip install gym['atari']
RUN pip install -e .

#ENTRYPOINT ["python", "run_mp.py", "Boxing-v0", "1", "10", "18000", "4", "600", "true", "test", "./results/","test","no"]
ENTRYPOINT [ "/bin/sh", "-c"]
CMD ["/bin/bash"]
#python run_mp.py Boxing-v0 1 10 18000 4 600 true test ./results/ test no
#python run_mp.py Boxing-v0 1 1 18000 4 50 true test ./results/ ms_graph_config.json 