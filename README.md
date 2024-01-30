## Csgo Float Parser

### Installing / Getting started
> * git clone https://github.com/OlegAlyeynikov/csgo_float_parser.git

For Mac and Linux you have to do the same for "buy_module", "check_float_from_listing", "csgo_django_server", "task_manager" projects:

> * cd path/to/project
> * python3 -m venv .venv
> * source .venv/bin/activate
> * Initialize environment variables .env as you can see in the .env_example file
> * pip install -r requirements.txt

In "buy_module" project you need to change set_sessionid_cookies method in "steampy library":

    # in .../csgo_float/buy_item/.venv/lib/python3.11/site-packages/steampy/login.py
    def set_sessionid_cookies(self):
        community_domain = SteamUrl.COMMUNITY_URL[8:]
        store_domain = SteamUrl.STORE_URL[8:]
        community_cookie_dic = self.session.cookies.get_dict(domain = community_domain)
        store_cookie_dic = self.session.cookies.get_dict(domain = store_domain)
        for name in ('steamLoginSecure', 'sessionid', 'steamRefresh_steam', 'steamCountry'):
            cookie = self.session.cookies.get_dict()[name]
            if name in ["steamLoginSecure"]:
                store_cookie = create_cookie(name, store_cookie_dic[name], store_domain)
            else:
                store_cookie = create_cookie(name, cookie, store_domain)

            if name in ["sessionid", "steamLoginSecure"]:
                community_cookie = create_cookie(name, community_cookie_dic[name], community_domain)
            else:
                community_cookie = create_cookie(name, cookie, community_domain)
            
            self.session.cookies.set(**community_cookie)
            self.session.cookies.set(**store_cookie)

In "buy_module" project you need to change set_sessionid_cookies method in "steampy library":

    # in .../csgo_float/buy_item/.venv/lib/python3.11/site-packages/steampy/client.py:
    @login_required
    def accept_trade_offer(self, trade_offer_id: str) -> dict:
        trade = self.get_trade_offer(trade_offer_id)
        trade_offer_state = TradeOfferState(trade['response']['offer']['trade_offer_state'])
        if trade_offer_state is not TradeOfferState.Active:
            raise ApiException(f'Invalid trade offer state: {trade_offer_state.name} ({trade_offer_state.value})')

        partner = self._fetch_trade_partner_id(trade_offer_id)
        session_id = self._session.cookies.get_dict("steamcommunity.com")['sessionid']
        accept_url = f'{SteamUrl.COMMUNITY_URL}/tradeoffer/{trade_offer_id}/accept'
        params = {
            'sessionid': session_id,
            'tradeofferid': trade_offer_id,
            'serverid': '1',
            'partner': partner,
            'captcha': '',
        }
        headers = {'Referer': self._get_trade_offer_url(trade_offer_id)}

        response = self._session.post(accept_url, data=params, headers=headers).json()
        if response.get('needs_mobile_confirmation', False):
            return self._confirm_transaction(trade_offer_id)
        return response

To start:
    
> * python3 manage.py makemigrations 
> * python3 manage.py migrate 
> * python manage.py createsuperuser 
> * go to your.host:port
