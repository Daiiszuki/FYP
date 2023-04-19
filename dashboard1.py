import dash
from dash import html
from dash import dcc
from dash.dependencies import Input, Output
from binance import Client
import pandas as pd
import dash_bootstrap_components as dbc
from typing import Callable
import websocket
import json
import requests
# Initialize the Binance client with your API keys
client = Client(api_key='2lwYoKqvTr7stZZgeRLaEuqNKSrEgGLFspKfwgA56Jgc6o0mvI3M2pwtc7sj8YLy', api_secret='4HDkUHXquBvS4v7aSWjvhGJvbTEma0wzTIUh7U8emIwx2Agqi74hfSYhSgSgpJIT')




class BinanceSocketManager:
    BASE_URL = "wss://stream.binance.com:9443"

    def __init__(self, client):
        self._client = client
        self._socket = None

    def start_book_ticker_socket(self, symbol: str, callback: Callable):
        """Start a websocket for a symbol's bookTicker.

        :param symbol: str
        :param callback: function
        """
        endpoint = f"{self.BASE_URL}/ws/{symbol.lower()}@bookTicker"
        self._socket = websocket.WebSocketApp(endpoint, on_message=callback)
        self._socket.run_forever()


# Initialize the BinanceSocketManager
bm = BinanceSocketManager(client)



# Define the layout using the Bootstrap grid system
app = dash.Dash(__name__,  external_stylesheets=[dbc.themes.CYBORG])
app.layout = html.Div([

    dbc.Row([
        dbc.Col([
            dcc.Input(id='ticker-symbol', type='text', value='BTCUSDT', style={'font-size':'50px', "border":"0"}),
            html.Br(),
            html.Iframe(id='tradingview-widget', 
                src="https://s.tradingview.com/widgetembed/?frameElementId=tradingview_6ca63&symbol=BINANCE%3ABTCUSDT&interval=D&hidesidetoolbar=0&symboledit=0&saveimage=1&toolbarbg=f1f3f6&studies=%5B%5D&theme=dark&background=#000000=1&timezone=Africa%2FJohannesburg&withdateranges=1&showpopupbutton=1&width=780&height=410&locale=en&utm_source=www.tradingview.com&utm_medium=widget_new&utm_campaign=chart&utm_term=BINANCE%3ABTCUSDT",
                style={'width': '100%', 'height': '755px', 'border': '1px solid #383838', "padding-top": "0", 'background-color': '#000000'}),
        ], width=11
        
        
        , style={ "padding-left": "40%"}),
        dbc.Col([
            html.H3('',style={'text-align':'center'}),
            dcc.Interval(id='orderbook-interval', interval=5000, n_intervals=0),
            html.Table(id='orderbook-table', style={'width': '100%'})
        ], width=1, style={"padding-top": "9%", "padding-right":"0"}),
    ], style={'margin': '0', "padding-top": "0", "padding-left":"0"}, ),
])

# Define the callback to update the TradingView widget
@app.callback(
    Output('tradingview-widget', 'src'),
    [Input('ticker-symbol', 'value')]
)
def update_tradingview_widget(ticker_symbol):
    src = f"https://s.tradingview.com/widgetembed/?frameElementId=tradingview_6ca63&symbol={ticker_symbol}&hidesidetoolbar=0&symboledit=0&saveimage=1&toolbarbg=f1f3f6&studies=%5B%5D&theme=dark&background=#000000=1&timezone=Africa%2FJohannesburg&withdateranges=1&showpopupbutton=1&width=780&height=410&locale=en&utm_source=www.tradingview.com&utm_medium=widget_new&utm_campaign=chart&utm_term={ticker_symbol}"
    return src



# Define the callback to update the order book table
@app.callback(
    Output('orderbook-table', 'children'),
    [Input('orderbook-interval', 'n_intervals')],
    [dash.dependencies.State('ticker-symbol', 'value')]
)

def update_order_book_table(n_intervals, ticker_symbol):
    global bids, asks
    # Define the WebSocket endpoint URL
    ws_url = 'wss://stream.binance.com:9443/ws/{}@depth'.format(ticker_symbol.lower())
    # Define the initial order book
    order_book = json.loads(requests.get('https://api.binance.com/api/v3/depth', params={'symbol': ticker_symbol, 'limit': 5}).text)
    bids = pd.DataFrame(order_book['bids'], columns=['Price', 'Quantity'])
    asks = pd.DataFrame(order_book['asks'], columns=['Price', 'Quantity'])
    # Create the WebSocket connection
    ws = websocket.WebSocketApp(ws_url, on_message=on_message)
    ws.run_forever()
    # Show only top 5 bids and asks
    top_bids = bids.head(10)
    top_bids.shape
    top_asks = asks.head(10)
    # Highlight highest bid and lowest ask
    highest_bid = top_bids['Price'].max()
    lowest_ask = top_asks['Price'].min()
    current_price = (float(highest_bid) + float(lowest_ask)) / 2
    # Format the price values to one decimal point
    top_bids.loc[:, 'Price'] = top_bids['Price'].astype(float).round(2)
    top_asks.loc[:, 'Price'] = top_asks['Price'].astype(float).round(2)
    # Create the bids table
    bids_table = html.Table(
        # Header
        [html.Tr([html.Th('Bid', style={'padding-right': '10px', "padding-left":"10px"}), html.Th('Qty', style={'padding-right': '10px', "padding-left":"10px"})]) ] +
        # Body
        [html.Tr([html.Td(top_bids.iloc[i]['Price'], style={'padding-right': '10px', 'padding-left': '10px', 'padding-top': '5px', 'padding-bottom': '5px'}), 
            html.Td(round(float(top_bids.iloc[i]['Quantity']), 2), style={'padding-right': '20px', 'padding-left': '20px', 'padding-top': '5px', 'padding-bottom': '5px'})
        ],
            style={'background-color': 'green' if top_bids.iloc[i]['Price'] == highest_bid else 'none'}
        )
        for i in range(len(top_bids))], style={"color":"#2fff00" , "font-size":"25px"})
    # Create the current price table
    current_price_table = html.Table(    [html.Tr([html.Th('Current Price', style={'padding-right': '10px', "padding-left":"10px"}), html.Th('Spread', style={'padding-right': '10px', "padding-left":"10px"})]) ] +
    # Body
    [html.Tr([html.Td('${:,.1f}'.format(current_price), style={'padding-right': '10px', 'padding-left': '10px', 'padding-top': '5px', 'padding-bottom': '5px', 'color':'#bfff00', "font-size":"35px"}),         html.Td('${:,.1f}'.format(float(lowest_ask) - float(highest_bid)), style={'padding-right': '20px', 'padding-left': '20px', 'padding-top': '5px', 'padding-bottom': '5px'})    ])])
    # Create the asks table
    asks_table = html.Table(
        # Header
        [html.Tr([html.Th('Ask', style={'padding-right': '10px', "padding-left":"10px"}), html.Th('Qty', style={'padding-right': '10px', "padding-left":"10px"})]) ] +
        # Body
        [html.Tr([html.Td(top_asks.iloc[i]['Price'], style={'padding-right': '10px', 'padding-left': '10px', 'padding-top': '5px', 'padding-bottom': '5px'}), 
            html.Td(round(float(top_asks.iloc[i]['Quantity']), 2), style={'padding-right': '20px', 'padding-left': '20px', 'padding-top': '5px', 'padding-bottom': '5px'})
        ],
            style={'background-color': 'red' if top_asks.iloc[i]['Price'] == lowest_ask else 'none'}
        )
        for i in range(len(top_asks))], style={"color":"#ff0000", "font-size":"25px"})
# Return the HTML layout
    return html.Div([bids_table, current_price_table, asks_table], style={"height": "480px","padding-left":"0"})

# Define the on_message callback function for the WebSocket
def on_message(ws, message):
   
    try:
        data = json.loads(message)
    except json.decoder.JSONDecodeError:
        return
    if data['e'] == 'depthUpdate':
        for bid in data['b']:
            bids.loc[bids['Price'] == bid[0], 'Quantity'] = bid[1]
            if bid[1] == '0.00000000':
                bids = bids[bids['Quantity'] != '0.00000000']
        for ask in data['a']:
            asks.loc[asks['Price'] == ask[0], 'Quantity'] = ask[1]
            if ask[1] == '0.00000000':
                asks = asks[asks['Quantity'] != '0.00000000']
        
        # Show only top 10 bids and asks
        top_bids = bids.sort_values('Price', ascending=False).head(10).reset_index(drop=True)
        top_asks = asks.sort_values('Price', ascending=True).head(10).reset_index(drop=True)
        
        # Highlight highest bid and lowest ask
        highest_bid = top_bids['Price'].max()
        lowest_ask = top_asks['Price'].min()
        top_bids['Price'] = top_bids['Price'].apply(lambda x: f'{x:.2f}' if x == highest_bid else f'{x:.8f}')
        top_asks['Price'] = top_asks['Price'].apply(lambda x: f'{x:.2f}' if x == lowest_ask else f'{x:.8f}')
        
        # Combine the top bids and asks into a single table
        orderbook = pd.concat([top_bids.rename(columns={'Price': 'Bids', 'Quantity': 'Bid Quantity'}),
                               top_asks.rename(columns={'Price': 'Asks', 'Quantity': 'Ask Quantity'})], axis=1)
        
        # Convert the table to an HTML table and display it in the app
        html_table = html.Table([
            html.Thead(html.Tr([html.Th(col) for col in orderbook.columns])),
            html.Tbody([
                html.Tr([
                    html.Td(orderbook.iloc[i][col]) for col in orderbook.columns
                ]) for i in range(len(orderbook))
            ])
        ])
        return html_table

if __name__ == '__main__':
    app.run_server(debug=True)
