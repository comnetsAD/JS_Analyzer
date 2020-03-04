# JS Analyzer
This is a tool built by ComNets AD lab @ NYUAD to help in the classification of JavaScript. The tool allows the user to visualize the enabling and disabling of individual scripts.

## Chrome Driver Installation
You need to have the right version of chrome driver to install. You can refer to the following page for more details.
https://chromedriver.chromium.org/downloads/version-selection

Once you have the right chrome driver, you need to locate it in a location that is in your system path. You can refer to the following page for more details.
http://jonathansoma.com/lede/foundations-2017/classes/more-scraping/selenium/

## Start the local proxy
Enter the following command:
```
$ mitmdump --mode upstream:10.224.41.171:8080 --set upstream_cert=false --sl-insecure --scripts proxy_setup.py
```

## Installing the proxy certificate
To connect to the proxy, do the following (instructions below are for macOS):
Go to your WiFi, open network preferences, choose proxies, and check the following:

Web Proxy (HTTP)
Secure Web Proxy (HTTPS)

For each of the checked options, you need to enter the following IP: 10.224.41.171 and then the port number (in the space after ":", which is: 8080. Click OK and then click Apply.

Open chrome browser and visit: mitm.it to install the required certificate. When the proper certificate is downloaded, you are required to open it, choose trust, and select "Always Trust".

Once you have installed the certificate, you may revert your network preferences back to the default.

## MySQL Installation

To install using homebrew, run the following:
```
$ brew install mysql
```
To start the server
```
$ mysql.server start
```
Change config.py to use your login credentials

## Download ML Classification Model

The model exceeds Github's maximum file size limit, so it can be found here.

https://drive.google.com/file/d/1Pta5pE9vQIAhUFwJEGqXZQmuys_2KMEW/view?usp=sharing

Make sure to save it in this repository folder.

## Start JS Analyzer
Enter the following command:
```
$ python3 analysisTool/analysis_tool.py
```

Once the tool is initiated, enter a website into the window and click "Analyze page" to see how the page looks with all scripts removed. Select scripts to display the content of the script and click "Apply Selection" to reload the page with the selected scripts enabled.

## Clear cache
This repo includes a script that allows you to clear the local proxy cache. To run the script, enter the following:
```
$ python3 clear_cache.py
```

## Troubleshooting
If you encounter a proxy certification error that prevents you from running the tool, repeat the proxy certificate installation steps and replace the IP address with your local IP: 127.0.0.1