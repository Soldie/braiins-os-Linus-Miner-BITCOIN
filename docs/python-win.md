## Download and install Python

1. [Download Python](https://www.python.org/downloads/windows/) (version 3.5.4 is recommended)
2. Run the downloaded installer
3.  Click 'Customize installation'
4. Check if 'pip' is selected for installation
5. Select 'Add Python to environment variables'
6. Finish the installation

## Check if python is in your PATH
  After the installation is complete double check to make sure you see python in your PATH.
  You can find your path by opening your *Control panel
  -> System and Security -> System -> Advanced System Settings -> Environment Variables -> Selecting Path -> Edit*.

## Install the environment
Run command line (cmd) and install virtualenv.

```
pip install virtualenv
```

The output is expected to include:


```
Installing collected packages: virtualenv
Successfully installed virtualenv-16.0.0
```

Install virtualenvwrapper-win:

```
pip install virtualenvwrapper-win
```

The output is expected to include:

```
Installing collected packages: virtualenvwrapper-win
  Running setup.py install for virtualenvwrapper-win ... done
Successfully installed virtualenvwrapper-win-1.2.5
```