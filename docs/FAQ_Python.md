# Frequently Asked Questions (FAQ)

### **Why do we work in a virtual environment?**
A virtual environment is a dedicated space on your computer for this project. It helps manage all the necessary tools and packages for the ANIN drought algorithms without interfering with other projects or programs on your system. Using a virtual environment prevents conflicts between different versions of Python or packages, ensuring that the project runs smoothly and consistently.

<!-- ### **How do I find the location of my Python installation?**
Open a separate Command Prompt window by pressing `Win + R`, type `cmd`, and press `Enter`. Then, run the following command:
``` py
where python
```
This command will list all installed Python paths, which may look like this:

```
C:\Python27\python.exe
C:\Users\<YourUsername>\AppData\Local\Programs\Python\Python38\python.exe
C:\Users\<YourUsername>\.pyenv\pyenv-win\shims\python
C:\Users\<YourUsername>\AppData\Local\Programs\Python\Python312\python.exe
```
To copy the path of the latest Python version (e.g., Python312), right-click in the Command Prompt window, select `Mark`, highlight the path, and then right-click again to copy the highlighted text to your clipboard. -->

### **How often to I need to activate the virtual environment?**
You need to activate the virtual environment every time you start a new session or open your terminal to work on the ANIN drought algorithms. Activating the virtual environment is crucial because it isolates the specific tools, libraries, and Python version required for the project.

If the virtual environment is not activated, your system will use the global Python installation and packages, which might not be compatible with the project's requirements. Activating the virtual environment ensures that you are using the correct setup, preventing issues such as version conflicts or missing dependencies.