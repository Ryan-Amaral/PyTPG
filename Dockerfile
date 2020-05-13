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
RUN pip install IPython
RUN pip install gym['atari']
RUN pip install -e .

ENTRYPOINT ["python", "run_mp.py"]
