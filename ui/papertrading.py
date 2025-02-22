import discord
import asyncio
import aiohttp
import json
from datetime import datetime
from discord import ui
from discord.ui import Button, button, View
from utils import DBClient
db = DBClient.db
# Configuration Constants
# TODO: put this in a config file
ALPHA_VANTAGE_API_KEY = os.getenv('ALPHA_VANTAGE_API_KEY')
RAPIDAPI_KEY = os.getenv('RAPIDAPI_KEY')
MIN_TRADE_AMOUNT = 1
MAX_TRADE_AMOUNT = 100000
TRADE_COOLDOWN = 5
DEMO_MODE = True
MOCK_PRICES = {
    "AAPL": 175.50,
    "GOOGL": 140.25,
    "MSFT": 380.75,
    "AMZN": 145.30,
    "TSLA": 240.45,
    "META": 485.60,
    "NVDA": 820.30,
    "AMD": 175.25
}
class StockPortfolioView(View):
    def __init__(self, authorid):
        super().__init__(timeout=None)
        self.authorid = authorid
        self.last_trade_time = {}

    @button(label="Buy Stocks", style=discord.ButtonStyle.primary, custom_id="buy_stocks", emoji="📈")
    async def buy_stocks(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.authorid:
            return await interaction.response.send_message("This isn't your trading session!", ephemeral=True)
        
        current_time = datetime.now().timestamp()
        if self.authorid in self.last_trade_time:
            time_diff = current_time - self.last_trade_time[self.authorid]
            if time_diff < TRADE_COOLDOWN:
                return await interaction.response.send_message(
                    f"Please wait {TRADE_COOLDOWN - int(time_diff)} seconds before trading again!",
                    ephemeral=True
                )
        
        self.last_trade_time[self.authorid] = current_time
        await interaction.response.send_modal(BuyStocksModal(self.authorid))

    @button(label="Sell Stocks", style=discord.ButtonStyle.danger, custom_id="sell_stocks", emoji="📉")
    async def sell_stocks(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.authorid:
            return await interaction.response.send_message("This isn't your trading session!", ephemeral=True)

        current_time = datetime.now().timestamp()
        if self.authorid in self.last_trade_time:
            time_diff = current_time - self.last_trade_time[self.authorid]
            if time_diff < TRADE_COOLDOWN:
                return await interaction.response.send_message(
                    f"Please wait {TRADE_COOLDOWN - int(time_diff)} seconds before trading again!",
                    ephemeral=True
                )

        self.last_trade_time[self.authorid] = current_time
        await interaction.response.send_modal(SellStocksModal(self.authorid))

    @button(label="View Portfolio", style=discord.ButtonStyle.secondary, custom_id="view_portfolio", emoji="📊")
    async def view_portfolio(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.authorid:
            return await interaction.response.send_message("This isn't your trading session!", ephemeral=True)
        c = db["trading"]
        portfolio = c.find_one({"user_id": interaction.user.id, "guild_id": interaction.guild.id})
        
        if not portfolio or not portfolio.get("positions", {}):
            return await interaction.response.send_message("You don't have any positions yet!", ephemeral=True)
        c_users = db["users"]
        user = c_users.find_one({"id": interaction.user.id, "guild_id": interaction.guild.id})
        
        embed = discord.Embed(title="Your Portfolio", color=0x00ff00)
        embed.add_field(name="Available Balance", value=f"${user['wallet']:,.2f}", inline=False)
        
        total_value = 0
        for symbol, position in portfolio["positions"].items():
            price = await get_stock_price(symbol)
            if price:
                current_value = position["shares"] * price
                total_value += current_value
                profit_loss = current_value - (position["shares"] * position["average_price"])
                
                embed.add_field(
                    name=f"{symbol}",
                    value=f"Shares: {position['shares']}\n"
                          f"Avg Price: ${position['average_price']:.2f}\n"
                          f"Current Price: ${price:.2f}\n"
                          f"P/L: ${profit_loss:.2f} ({(profit_loss/current_value)*100:.1f}%)",
                    inline=False
                )
        embed.add_field(name="Total Portfolio Value", value=f"${total_value:.2f}", inline=False)
        embed.add_field(name="Total Account Value", value=f"${(total_value + user['wallet']):.2f}", inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)

class BuyStocksModal(ui.Modal, title="Buy Stocks"):
    def __init__(self, authorid):
        super().__init__()
        self.authorid = authorid

    symbol = ui.TextInput(label="Stock Symbol", placeholder="e.g. AAPL", min_length=1, max_length=5)
    shares = ui.TextInput(label="Number of Shares", placeholder="e.g. 10")

    async def on_submit(self, interaction: discord.Interaction):
        if interaction.user.id != self.authorid:
            return await interaction.response.send_message("This isn't your trading session!", ephemeral=True)
        symbol = self.symbol.value.upper()
        try:
            shares = float(self.shares.value)
            if not MIN_TRADE_AMOUNT <= shares <= MAX_TRADE_AMOUNT:
                return await interaction.response.send_message(
                    f"Please enter between {MIN_TRADE_AMOUNT} and {MAX_TRADE_AMOUNT} shares!",
                    ephemeral=True
                )
        except ValueError:
            return await interaction.response.send_message("Please enter a valid number of shares!", ephemeral=True)

        price = await get_stock_price(symbol)

        if not price:
            return await interaction.response.send_message("Invalid stock symbol or API error!", ephemeral=True)
            
        total_cost = price * shares
        c = db["users"]

        user = c.find_one({"id": interaction.user.id, "guild_id": interaction.guild.id})
        if not user or user["wallet"] < total_cost:
            return await interaction.response.send_message(
                f"Insufficient funds! You need ${total_cost:,.2f} but have ${user['wallet']:,.2f}",
                ephemeral=True
            )
        c = db["trading"]

        portfolio = c.find_one({"user_id": interaction.user.id, "guild_id": interaction.guild.id})
        
        if not portfolio:
            portfolio = {
                "user_id": interaction.user.id,
                "guild_id": interaction.guild.id,
                "positions": {}
            }
            c.insert_one(portfolio)
        if symbol in portfolio["positions"]:
            current_position = portfolio["positions"][symbol]
            new_shares = current_position["shares"] + shares
            new_average_price = ((current_position["shares"] * current_position["average_price"]) + total_cost) / new_shares
            portfolio["positions"][symbol] = {
                "shares": new_shares,
                "average_price": new_average_price
            }
        else:
            portfolio["positions"][symbol] = {
                "shares": shares,
                "average_price": price
            }
        c.update_one(
            {"user_id": interaction.user.id, "guild_id": interaction.guild.id},
            {"$set": {"positions": portfolio["positions"]}}
        )
        user["wallet"] -= total_cost
        c = db["users"]
        c.update_one(
            {"id": interaction.user.id, "guild_id": interaction.guild.id},
            {"$set": {"wallet": user["wallet"]}}
        )
        await interaction.response.send_message(
            f"Successfully bought {shares} shares of {symbol} at ${price:.2f} per share.\n"
            f"Total cost: ${total_cost:.2f}\n"
            f"Remaining balance: ${user['wallet']:,.2f}",
            ephemeral=True
        )

class SellStocksModal(ui.Modal, title="Sell Stocks"):
    def __init__(self, authorid):
        super().__init__()
        self.authorid = authorid
    symbol = ui.TextInput(label="Stock Symbol", placeholder="e.g. AAPL", min_length=1, max_length=5)
    shares = ui.TextInput(label="Number of Shares", placeholder="e.g. 10")
    async def on_submit(self, interaction: discord.Interaction):
        if interaction.user.id != self.authorid:
            return await interaction.response.send_message("This isn't your trading session!", ephemeral=True)
        symbol = self.symbol.value.upper()
        try:
            shares = float(self.shares.value)
            if shares <= 0:
                raise ValueError("Shares must be positive")
        except ValueError:
            return await interaction.response.send_message("Please enter a valid number of shares!", ephemeral=True)
        c = db["trading"]
        portfolio = c.find_one({"user_id": interaction.user.id, "guild_id": interaction.guild.id})
        
        if not portfolio or symbol not in portfolio["positions"]:
            return await interaction.response.send_message("You don't own this stock!", ephemeral=True)
        current_position = portfolio["positions"][symbol]
        if current_position["shares"] < shares:
            return await interaction.response.send_message(
                f"You don't have enough shares! You own {current_position['shares']} shares.",
                ephemeral=True
            )
        price = await get_stock_price(symbol)
        if not price:
            return await interaction.response.send_message("Invalid stock symbol or API error!", ephemeral=True)
        total_value = price * shares
        new_shares = current_position["shares"] - shares
        if new_shares == 0:
            del portfolio["positions"][symbol]
        else:
            portfolio["positions"][symbol]["shares"] = new_shares
        c.update_one(
            {"user_id": interaction.user.id, "guild_id": interaction.guild.id},
            {"$set": {"positions": portfolio["positions"]}}
        )
        c = db["users"]
        user = c.find_one({"id": interaction.user.id, "guild_id": interaction.guild.id})
        user["wallet"] += total_value
        c.update_one(
            {"id": interaction.user.id, "guild_id": interaction.guild.id},
            {"$set": {"wallet": user["wallet"]}}
        )
        profit_loss = (price - current_position["average_price"]) * shares
        await interaction.response.send_message(
            f"Successfully sold {shares} shares of {symbol} at ${price:.2f} per share.\n"
            f"Total value: ${total_value:.2f}\n"
            f"Profit/Loss: ${profit_loss:.2f}\n"
            f"New balance: ${user['wallet']:,.2f}",
            ephemeral=True
        )

async def get_stock_price_av(symbol):
    """Get current stock price using Alpha Vantage API or mock data"""
    if DEMO_MODE and symbol in MOCK_PRICES:
        return MOCK_PRICES[symbol]
        
    url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={ALPHA_VANTAGE_API_KEY}"
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url) as response:
                data = await response.json()
                if "Global Quote" in data and "05. price" in data["Global Quote"]:
                    return float(data["Global Quote"]["05. price"])
                return None
        except:
            return None

async def get_stock_price(symbol): 
    """Get current stock price using Yahoo Finance API via RapidAPI or mock data."""
    if DEMO_MODE and symbol in MOCK_PRICES:
        return MOCK_PRICES[symbol]
        
    url = f"https://apidojo-yahoo-finance-v1.p.rapidapi.com/stock/v2/get-summary?symbol={symbol}&region=US"
    headers = {
        "x-rapidapi-host": "apidojo-yahoo-finance-v1.p.rapidapi.com",
        "x-rapidapi-key": RAPIDAPI_KEY
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, headers=headers) as response:
                data = await response.json()
                if "price" in data and "regularMarketPrice" in data["price"]:
                    return float(data["price"]["regularMarketPrice"]["raw"])
                return None
        except Exception as e:
            print(f"Error fetching stock price: {e}")
            return None

async def start_paper_trading(ctx):
    """
    Command to start paper trading session
    Usage: !trade or /trade
    """
    c = db["users"]
    user = c.find_one({"id": ctx.author.id, "guild_id": ctx.guild.id})
    
    if not user:
        return await ctx.send("get outa here brokie")
    embed = discord.Embed(
        title="Paper Trading",
        description="Welcome to paper trading! Trade stocks with your existing balance.\n"
                   "Use the buttons below to buy/sell stocks and view your portfolio.",
        color=0x00ff00
    )
    embed.add_field(
        name="Available Balance",
        value=f"${user['wallet']:,.2f}",
        inline=False
    )
    if DEMO_MODE:
        embed.add_field(
            name="Available Demo Stocks",
            value="\n".join([f"{symbol}: ${price:.2f}" for symbol, price in MOCK_PRICES.items()]),
            inline=False
        )
    view = StockPortfolioView(ctx.author.id)
    await ctx.send(embed=embed, view=view)