## Csgo Float Parser

### Get float, analyze the Steam Market, buy items automatically.

<p>The project consists of four independent projects that transmit commands to each other via ports.  Each project has its own virtual environment.  
This was done in order to separate the chain of asynchronous loops and also to implement the ability to parse a large number of objects.</p>

<p>search_changes_on_pages - uses Steam Search to continuously scrape the total quantity of every item on the platform.  
If it finds changes, it sends the json object to the listing project. </p>

<p>check_float_from_listing - takes a command and makes a request to the steam listing endpoint for a specific item.  
It compares specified search conditions such as price and float range, and if the conditions match, it sends a command to the buy module project.</p>

<p>buy_item - when receiving a command, immediately tries to buy the item. </p>

<p>csgo_django_server - provides a simple interface for management.</p>

   

### Installing / Getting started

For Mac and Linux you have to do the same for "buy_module", "check_float_from_listing", "csgo_django_server", "search_changes_on_pages" projects:

> * git clone https://github.com/OlegAlyeynikov/csgo_float_parser.git
> * cd path/to/project
> * python3 -m venv .venv
> * source .venv/bin/activate
> * Initialize environment variables .env as you can see in the .env_example file
> * pip install -r requirements.txt
> * Add proxies to /csgo_float/proxies_list.txt

You will need to install CSGOFloat is a free and open source API service that allows you to obtain the float and paint seed of any CSGO item using its inspect link.

> * https://github.com/csfloat/inspect

To start:

> * Generate your django key and add to .env file:
> * python manage.py shell -c "from django.core.management import utils; print(utils.get_random_secret_key())"
> * python3 manage.py makemigrations 
> * python3 manage.py migrate 
> * python manage.py createsuperuser 
> * go to your.host:port
