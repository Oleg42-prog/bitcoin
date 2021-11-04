import networkx as nx

from bitcoin import *
import random

from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
from Crypto.Signature import pkcs1_15
import os

from bokeh.models import Circle, MultiLine
from bokeh.plotting import figure, from_networkx, show
from bokeh.layouts import row

satoshi = Agent(name="Satoshi")

names = ["Судзуки", "Танака", "Ямамото", "Ватанабэ", "Сайто", "Сато", "Сасаки", "Кудо", "Такахаси", "Кобаяси", "Като", "Ито", "Мураками"]
agents = [Agent(name=n) for n in names]

time = 0

first_transaction = ForefatherTransaction(recipient=TransactionElement(satoshi, 50), time=time)
forefather_skey = RSA.generate(1024, os.urandom)
forefather_pkey = forefather_skey.publickey()
forefather_h = SHA256.new()
forefather_h.update(bytes(first_transaction.serialize(), encoding='utf-8'))
forefather_signature = pkcs1_15.new(forefather_skey).sign(forefather_h)
signature_first_transaction = SignatureTransaction(first_transaction, forefather_signature)
forefather_hash = signature_first_transaction.hash

oleg = MinerAgent(name="Oleg", forefather_hash=forefather_hash)
hitler = Villain(name="Гитлер", forefather_hash=forefather_hash)
miners_names = ["Лера", "Настя", "Оля", "Катя"]
miners = [MinerAgent(name=n, forefather_hash=forefather_hash) for n in miners_names]
miners += [oleg]
agents += [hitler]
agents += miners

satoshi.updateTransactions([signature_first_transaction])

time += 1

interval = int(input('interval: '))

for i in range(5):
	satoshi.createTransaction(random.choice(agents), time)


for agent in agents:
	agent.updateTransactions(satoshi.transactions)

for i in range(interval):
	time += 1
	for j in range(3):
		x = random.choice(agents)
		y = random.choice(agents)

		if x.hash != y.hash:
			x.createTransaction(y, time)

		x.updateTransactions(y.transactions)
		y.updateTransactions(x.transactions)

		x.updateBlocks(y.blocks)
		y.updateBlocks(x.blocks)

	for m in miners:
		m.mining(time)

transactions = []
for agent in agents:
	transactions += agent.transactions
transactions = list(set(transactions))


blocks = []
for miner in miners:
	blocks += miner.blocks
blocks = list(set(blocks))


def blockParents(block, l=[]):
	if block.parent is None:
		return l + [block]
	else:
		return blockParents(block.parent, l + [block])

last_block = sorted(blocks, key=lambda b: b.age, reverse=True)[0]
highest_network = blockParents(last_block)
highest_network_transactions = []
for block in highest_network:
	highest_network_transactions += block.transactions

highest_network_transactions_hash = list(map(lambda t: t.hash, highest_network_transactions))

G = nx.DiGraph(directed=True)
for t in range(len(transactions)):
	s = transactions[t]
	
	if transactions[t].hash == forefather_hash:
		sender = "Forefather"
		remainder = ""
	else:
		sender = str(s.sender)
		remainder = str(s.remainder)
	
	G.add_node(t, sender=sender, recipient=str(s.recipient), 
		remainder=remainder, 
		signature=s.signature.hex()[:20], 
		hash=s.hash, sha256=s.sha256_hex[:20],
		time=s.time)

def verify(transaction):
	try:
		pkcs1_15.new(transaction.sender.agent.pkey).verify(transaction.crypto_hash, transaction.signature)
	except ValueError as e:
		return False
	else:
		return True

edge_attrs = {}
for t1 in range(len(transactions)):
	for t2 in range(len(transactions)):
		if t1 != t2:
			if transactions[t1].hash != forefather_hash:
				if transactions[t1].parent.hash == transactions[t2].hash:
					G.add_edge(t2, t1)

					if verify(transactions[t1]):
						edge_attrs[(t2, t1)] = "darkgrey"
					else:
						edge_attrs[(t2, t1)] = "red"

					if transactions[t1].hash in highest_network_transactions_hash:
						edge_attrs[(t2, t1)] = "blue"

					if transactions[t2].hash == forefather_hash:
						edge_attrs[(t2, t1)] = "black"


nx.set_edge_attributes(G, edge_attrs, "edge_color")

BlockGraph = nx.DiGraph(directed=True)
for i in range(len(blocks)):
	block = blocks[i]
	BlockGraph.add_node(i, owner=block.owner.name, age=block.age, count=len(block.transactions), stime=block.stime, etime=block.etime)

block_edge_attrs = {}
for i in range(len(blocks)):
	for j in range(len(blocks)):
		if i != j:
			if blocks[i].parent != None:
				if blocks[i].parent.hash == blocks[j].hash:
					BlockGraph.add_edge(j, i)
					if blocks[i] in highest_network:
						block_edge_attrs[(j, i)] = "blue"
					else:
						block_edge_attrs[(j, i)] = "red"						
nx.set_edge_attributes(BlockGraph, block_edge_attrs, "edge_color")


plot = figure(width=800, height=600, x_range=(-1.2, 1.2), y_range=(-1.2, 1.2),
              x_axis_location=None, y_axis_location=None, toolbar_location=None,
              title="Graph Interaction Demo", background_fill_color="#efefef", tooltips="@sender -><br>@recipient, <br>@remainder <br> s: @signature <br> h: @hash <br> sh: @sha256 <br> t: @time")
plot.grid.grid_line_color = None

graph_renderer = from_networkx(G, nx.spring_layout, scale=1, center=(0, 0))
graph_renderer.node_renderer.glyph = Circle(size=15, fill_color="lightblue")
graph_renderer.edge_renderer.glyph = MultiLine(line_color="edge_color",
                                               line_alpha=0.8, line_width=1.5)

plot.renderers.append(graph_renderer)



plot_block = figure(width=800, height=600, x_range=(-1.2, 1.2), y_range=(-1.2, 1.2),
              x_axis_location=None, y_axis_location=None, toolbar_location=None,
              title="Graph Interaction Demo", background_fill_color="#efefef", tooltips="@owner: @age <br> c: @count <br> st: @stime <br> et: @etime")
plot_block.grid.grid_line_color = None

block_graph_renderer = from_networkx(BlockGraph, nx.spring_layout, scale=1, center=(0, 0))
block_graph_renderer.node_renderer.glyph = Circle(size=15, fill_color="lightblue")
block_graph_renderer.edge_renderer.glyph = MultiLine(line_color="edge_color",
                                               line_alpha=0.8, line_width=1.5)

plot_block.renderers.append(block_graph_renderer)



show(row(plot, plot_block))