@echo off

:: Download and extract repository
wget https://github.com/ModerNews/Wybory/archive/refs/heads/main.zip
tar -xf main.zip
cd Wybory-main/app

:: Activate virtual enviroment
python3.10 venv /venv
.%0\..\venv/Scripts/activate.bat

:: install dependencies and run the program
pip install -r %0\..\requirements.txt
python runner.py