# JS Cleaner
This is a tool built by ComNets AD lab @ NYUAD to help in the classification of JavaScript. The tool allows the user to visualize the enabling and disabling of individual scripts.

## Database Setup

This tool uses a mysql database. Mysql can be installed using homebrew:

    $ brew install mysql

Start mysql:

    $ brew services start mysql

Set a strong password for your mysql root account. Make sure that the password is something that you will remember.

    $ mysqladmin -u root password 'newpassword'

Log into mysql. You will be prompted to enter your password.

    $ mysql -u root -p

Create a new database with the name JSCleaner.

    > CREATE DATABASE JSCleaner;
    
Import the script located in proxy/caching.mysql.

    > source proxy/caching.sql;

## Browser Setup

Your Firefox browser must be set up to use the proxy.

1. Open the browser and navigate to about:preferences.
2. Under General > Network Settings, click on the "Settings" button.
3. Check the "Manual Proxy Configuration" radio button and enter "127.0.0.1" in the HTTP Proxy field and "9999" in the Port field.
4. Make sure the "Use this proxy server for all protocols" box is checked.
5. Click "OK".
6. Under Privacy & Security > Certificates, click on the "View Certificates..." button.
7. Navigate to the "Authorities" tab and click "Import...".
8. Select proxy/ca-local.pem located in this repository.
9. In the dialog box that opens, check the box that says "This certificate can identify websites", then click OK.

Your Firefox browser should now be configured to use the local proxy.

In analysisTool/JStool_v2.py, search for the line with the following text:

> fp = webdriver.FirefoxProfile

Replace the string in the parentheses with the path to the Firefox profile on your machine. The profile is typically located in /Users/Username/Library/Application Support/Firefox/Profiles/.

## Edit Config File

In analysisTool/config.py, create a new user and add your database password and firefox profile path. The firefox profile is typically located in /Users/Username/Library/Application Support/Firefox/Profiles/.

In analysisTool/JSTool_v2.py, change the name variable at the beginning of the code to be the name of the new user that you just created.

## Start JS Cleaner

Start the local proxy.

    $ python proxy/proxy.py

With the local proxy still running, start the tool.

    $ python3 analysisTool/JStool_v2.py

Enter a website into the window and click "Analyze page" to see how the page looks with all scripts removed. Click on a script button to display the content of the script and reload the page with that specific script enabled.
