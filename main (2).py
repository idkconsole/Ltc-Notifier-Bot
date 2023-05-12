import discord
import requests
from discord.ext import commands, tasks

intents = discord.Intents.all()

bot = commands.Bot(command_prefix="!", intents=intents)

last_hash = None
guild_id = 1106623710108057650
ltc_addy = 'LKSwveqwga6ixmviMACdcRH7vTzLqmANGK'

@bot.event
async def on_ready():
    print(f'{bot.user}')
    transaction_check.start()

@tasks.loop(seconds=60)
async def transaction_check():
    global last_hash
    response = requests.get(f'https://api.blockcypher.com/v1/ltc/main/addrs/{ltc_addy}/full').json()

    if 'txs' in response:
        latest_transaction = response['txs'][0]
        latest_hash = latest_transaction['hash']
        if latest_hash != last_hash:
            total_received = sum(output['value'] / 1e8 for output in latest_transaction['outputs'] if 'addresses' in output and ltc_addy in output['addresses'])
            ltc_to_usd_rate = requests.get('https://api.coingecko.com/api/v3/simple/price?ids=litecoin&vs_currencies=usd').json()['litecoin']['usd']
            total_received_usd = total_received * ltc_to_usd_rate
            if total_received > 0:
                await send_transaction_notification(latest_hash, total_received_usd)
            last_hash = latest_hash

async def send_transaction_notification(hash: str, amount: float):
    guild = bot.get_guild(guild_id)
    if guild:
        for channel in guild.text_channels:
            if channel.name == 'general':
                # get the LTC to USD exchange rate
                ltc_to_usd_rate = requests.get('https://api.coingecko.com/api/v3/simple/price?ids=litecoin&vs_currencies=usd').json()['litecoin']['usd']

                # get the transaction details
                transaction = requests.get(f'https://api.blockcypher.com/v1/ltc/main/txs/{hash}').json()
                # find the input address (sent from)
                if 'inputs' in transaction:
                    input_address = transaction['inputs'][0]['addresses'][0]  # assuming the first input is the sender

                embed = discord.Embed(title="New LTC Transaction", color=0000)
                embed.add_field(name="Hash", value=f"[{hash}](https://live.blockcypher.com/ltc/tx/{hash})", inline=False)
                embed.add_field(name="Amount", value=f"${amount:.2f}", inline=False)
                embed.add_field(name="Sent From", value=input_address, inline=False)
                embed.add_field(name="LTC Price", value=f"${ltc_to_usd_rate:.2f}", inline=False)
                await channel.send("@everyone", embed=embed)

bot.run('MTEwNjYyNDczMTU5NzI1NDcxNg.GfmiKI.e8ujiG4izxI1IGMXrr6JCNkSUNrEETxqiCFt7M')