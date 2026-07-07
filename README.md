# rsteye

  ![RstEyeApp](rsteye.png)

  - An App to take digital break
  - An App to remind users to take breaks and relax their eyes while working on the computer.

## General Info 

  - What is the purpose behind this project?
    
    > This project aims to explore various build systems, computer architectures, and operating systems available across the internet. Additionally, it will open a GIF with deep breathing instructions every hour, covering your entire screen.


# Usage Instructions

## Debian

### Set Environment Variables

  - `POPUP_DURATION`: This variable sets the duration for which you want the popup to appear. The default value is 60 seconds (1 minute). You must provide this value in seconds.

  - `POPUP_INTERVAL`: This variable sets the interval after which you want the popup to appear. The default value is 60 minutes. You must provide this value in minutes.

### Configure Environment Variables

  Set these environment variables in your shell configuration files (e.g., `.bashrc` or `.zshrc`). For example:

  ```sh
  export POPUP_DURATION=30
  export POPUP_INTERVAL=120
  ```

### Download and Install

  Download the `.deb` file from one of the stable https://github.com/RstEyeApp/rsteye/releases/ 
  
  and install it by running:

  ```sh
  sudo dpkg -i rsteye.deb
  ```

### Run the Application

  After installation, you can run `RstEyeApp &` from any terminal:
  
  you can use service file as well to start it in the background 

  reload systemctl using `sudo systemctl daemon-reload` and then start the service `sudo systemctl start rsteyeapp.service` (currently not working)

  *DO WAIT FOR FEW SEC(7-8) TO START*


# Development 

  - Debian 

    - create virtual env and install dependencies 
      - python3 -m venv .venv
      - source .venv/bin/activate
      - python3 -m pip install pillow pyinstaller python-dotenv

    - run below command to create a binary file to package it as deb package 
      `pyinstaller --name RstEyeApp --windowed --onefile --add-data "med.gif:." --add-data "rsteye.png:." --hidden-import=PIL.ImageTk --additional-hooks-dir=hooks app.py`    
    
    - create a deb package(`dpkg-deb --build rsteye`) after copying the binary to deb_package(rsteye) usr/bin and creating DEBIAN files  

    - DEBUG 
      - journalctl -u rsteye.service -b

  - Mac

     - Create a Virtual Environment and Install Dependencies
       - python3 -m venv .venv
       - source .venv/bin/activate
       - python3 -m pip install pillow pyinstaller python-dotenv
  
     - run
       `pyinstaller --name RstEyeApp --windowed --onefile --add-data "med.gif:." --add-data "rsteye.png:." --hidden-import=PIL.ImageTk --additional-hooks-dir=hooks app.py`
     
     - create an installer after following the below instructions 

        - Create scripts files
       
            Create postinstall, preinstall and user_input.applescript files 

        - Make the script files executable
        
            chmod +x mac_os_files/scripts/* 

        - Ensure the plist file is ready and accessible in mac_os_files

            Example: cp ./com.rsteye.rsteye.plist mac_os_files/

        - Build the installer package

            `pkgbuild --root dist/RstEyeApp.app \
         --scripts mac_os_files/scripts \
         --identifier com.rsteye.rsteye \
         --version 1.0 \
         --install-location /Applications/RstEyeApp \
         mac_os_files/RstEyeApp.pkg`

        - Final installer 
        
          `productbuild --distribution mac_os_files/distribution.xml \
             --resources mac_os_files/resources \
             --package-path mac_os_files \
             --version 1.0 \
             RstEyeAppInstaller.pkg`

    - DEBUG 
      - Check system logs:
        - sudo launchctl list | grep com.rsteye.rsteye
      - Check system logs:
        - log show --predicate 'process =="RstEyeApp"' --info --last 1h

    - Uninstall 
      - sudo launchctl unload /Library/LaunchDaemons/com.rsteye.rsteye.plist
      - sudo launchctl unload /Library/LaunchDaemons/com.rsteye.env.plist
      - sudo rm /Library/LaunchDaemons/com.rsteye.rsteye.plist
      - sudo rm /Library/LaunchDaemons/com.rsteye.env.plist



  - Windows

    - Create Virtual Environment and Install Dependencies
      - python -m venv .venv
      - .\.venv\Scripts\activate
      - python -m pip install pillow pyinstaller python-dotenv

    - Build PyInstaller Application

      - Run the following command to create a binary file:
        `pyinstaller --name RstEyeApp --onefile --add-data "med.gif;." --add-data "rsteye.png:." --hidden-import=PIL.ImageTk --additional-hooks-dir=hooks --icon=rsteye.ico app.py`

    - Install Inno setup(https://jrsoftware.org/isdl.php#stable) for windows and run below command to generate an installer 
      - "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" setup.iss


# App Structure 

```mermaid
sequenceDiagram
    participant User
    participant App
    participant ImageLoader

    User->>App: Clicks to load image
    App->>User: Shows popup with new message
    User->>App: Reads breathing exercise message
    App->>ImageLoader: Requests image
    ImageLoader->>App: Loads image
    App->>User: Displays image
