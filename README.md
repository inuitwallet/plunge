#Plunge

##UI for the Nu trust-less liquidity pool.

###Requirements
####[Python 2.7](https://www.python.org/download/releases/2.7/)
####[Kivy](http://kivy.org)
####[Requests](http://docs.python-requests.org/en/latest/)

###Setup
Install the requirements on your machine.  
Create a directory in the 'plunge' directory called 'client'.  
Clone a copy of [creons trustless liquidity client](https://github.com/creon-nu/nu-pool) and copy all the files in the 'python' directory to the new 'client' directory under 'plunge'.  
Run plunge.py.  
The command to run a Kivy application varies depending on your OS.  
There is more information on the [Kivy website](http://kivy.org/docs/gettingstarted/installation.html).  

###Configuration
Once you have run plunge.py, you will see the main UI.  
To go to the configuration, click on the top bar where the Nu logo is.  
The first configuration screen you see is for the global settings.  
To configure each exchange, you first need to enable them using the toggle switches under 'Active Exchanges'.  
Once you have enabled an exchange, select the Exchanges settings from the top dropdown menu (light grey, says 'Plunge Configuration').  
Enter the API keys and payout address details as well as any of the other settings you wish to change and click 'Close' (at the top next to the dropdown menu).  
  
To start the client, click the 'Start' button towards the bottom of the main page.  
The client will be configured based on the settings you have entered and will start.  
The client output will start to scroll below the 'Start/Stop' button.  
The statistics shown on the UI will begin to update.  

###Notice
This is a work in progress. The client interaction works but may break without warning.  
I am adding statistics to the UI when I can, I aim to add everything that is available from the server.  
  
Use with caution. the idea is that this client is trust-less so you remain in charge of your API keys.  
The server, client, ui and pool operator cannot see your secret keys so cannot interact with your money.  
However, money is at play so use wisely.  



