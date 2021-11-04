import uuid
from abc import ABC
import random
import copy

from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
from Crypto.Signature import pkcs1_15
import os

import json


class Network():
	
	@property
	def general_power(self):
		return self._general_power
	
	@property
	def blocks_count(self):
		return self._blocks_count
	
	def generateComplexity(self):
		return general_power / 100

	def generateReward(self):
		order_decreasing_reward = blocks_count // 10
		return 50 / 2 ** (order_decreasing_reward)

class Entity(ABC):
	
	@property
	def hash(self):
		return self._hash

	def __init__(self):
		self._hash = uuid.uuid4().hex

class TransactionElement():
	
	@property
	def agent(self):
		return self._agent
	
	@property
	def value(self):
		return self._value

	def __init__(self, agent, value: int):
		self._agent = agent
		self._value = value

	def __str__(self):
		return str(self._agent) + ': ' + str(self._value)

	def serialize(self):
		return json.dumps({'agent': self._agent.hash, 'value': self._value})


class ForefatherTransaction(Entity):
	
	@property
	def time(self):
		return self._time
	
	@property
	def recipient(self):
		return self._recipient

	@property
	def reward(self):
		return 10

	def __init__(self, recipient: TransactionElement, time):
		super(ForefatherTransaction, self).__init__()
		self._recipient = recipient
		self._time = time
		
	def __str__(self):
		return "Forefather" + " -> " + str(self._recipient)

	def show(self):
		return "Forefather" + " -> ", str(self._recipient)

	def serialize(self):
		return json.dumps({'sender': 'Forefather', 'recipient': self._recipient.serialize()})

	def sha256(self):
		h = SHA256.new()
		h.update(bytes(self.serialize(), encoding='utf-8'))
		return h

class Transaction(ForefatherTransaction):
	
	@property
	def remainder(self):
		return self._remainder

	@property
	def sender(self):
		return self._sender

	@property
	def parent(self):
		return self._parent

	@property
	def reward(self):
		return self._sender.value - self._remainder.value
	
	def __init__(self, parent: ForefatherTransaction, sender: TransactionElement,
	 recipient: TransactionElement, remainder: TransactionElement, time):
		super(Transaction, self).__init__(recipient, time)
		self._remainder = remainder
		self._sender = sender
		self._parent = parent

	def __str__(self):
		return str(self._sender) + " -> " + str(self._recipient) + ', ' + str(self._remainder)

	def serialize(self):
		return json.dumps({'parent': self._parent.hash, 'sender': self._sender.serialize(), 'recipient': self._recipient.serialize(), 'remainder': self._remainder.serialize()})

	def sha256(self):
		h = SHA256.new()
		h.update(bytes(self.serialize(), encoding='utf-8'))
		return h

# Decorator
class SignatureTransaction():
	
	@property
	def hash(self):
		return self._transaction.hash
	
	@property
	def time(self):
		return self._transaction.time
	
	@property
	def recipient(self):
		return self._transaction.recipient
	
	@property
	def remainder(self):
		return self._transaction.remainder

	@property
	def reward(self):
		return self._transaction.reward
	
	@property
	def sender(self):
		return self._transaction.sender
	
	@property
	def parent(self):
		return self._transaction.parent

	def serialize(self):
		return self._transaction.serialize()

	@property
	def transaction(self):
		return self._transaction

	@property
	def signature(self):
		return self._signature

	@property
	def crypto_hash(self):
		return self._transaction.sha256()

	@property
	def sha256_hex(self):
		return self._transaction.sha256().hexdigest()	
	
	def __init__(self, transaction: Transaction, signature):
		self._transaction = transaction
		self._signature = signature

	def serialize(self):
		return json.dumps({'parent': self._parent.hash, 'sender': self._sender, 'recipient': self._recipient, 'remainder': self._remainder})

	def __str__(self):
		return str(self._transaction)

class Agent(Entity):

	@property
	def pkey(self):
		return self._skey.publickey()

	@property
	def last_transaction(self):
		return self._last_transaction

	@property
	def name(self):
		return self._name
	
	@property
	def transactions(self):
		return list(set(self._transactions + self._income_transactions + self._outcome_transactions))

	@property
	def blocks(self):
		return self._blocks

	def __init__(self, name):
		super(Agent, self).__init__()
		self._skey = RSA.generate(1024, os.urandom)
		self._name = name
		self._income_transactions = []
		self._outcome_transactions = []
		self._transactions = []
		self._blocks = []

	def _signature(self, transaction):
		signature = pkcs1_15.new(self._skey).sign(transaction.sha256())
		return SignatureTransaction(transaction, signature)

	def _createTransactionFromIncome(self, agent, time):

		if self._income_transactions == []:
			return

		transaction = random.choice(self._income_transactions)
		
		new_transaction = Transaction(
			parent=transaction, 
			sender=transaction.recipient,
			recipient=TransactionElement(agent, transaction.recipient.value * 0.2),
			remainder=TransactionElement(self, transaction.recipient.value * 0.8),
			time=time
		)
		
		self._outcome_transactions.append(self._signature(new_transaction))
		self._income_transactions.remove(transaction)
		self._transactions.append(transaction)

	def _createTransactionFromOutcome(self, agent, time):

		if self._outcome_transactions == []:
			return

		transaction = random.choice(self._outcome_transactions)

		new_transaction = Transaction(
			parent=transaction,
			sender=transaction.remainder,
			recipient=TransactionElement(agent, transaction.remainder.value * 0.2),
			remainder=TransactionElement(self, transaction.remainder.value * 0.8),
			time=time
		)

		self._outcome_transactions.append(self._signature(new_transaction))
		self._outcome_transactions.remove(transaction)
		self._transactions.append(transaction)

	def createTransaction(self, agent, time):

		if self._income_transactions == []:
			self._createTransactionFromOutcome(agent, time)

		if self._outcome_transactions == []:
			self._createTransactionFromIncome(agent, time)

		if self._income_transactions != [] and self._outcome_transactions != []:
			if random.random() > 0.5:
				self._createTransactionFromIncome(agent, time)
			else:
				self._createTransactionFromOutcome(agent, time)

	def updateTransactions(self, transactions):
		new_transactions = list(set(transactions) - set(self.transactions))
		
		for t in new_transactions:
			if t.transaction.recipient.agent.hash == self.hash:
				self._income_transactions.append(t)
			else:
				self._transactions.append(t)


	def updateBlocks(self, blocks):
		new_blocks = list(set(blocks) - set(self.blocks))
		self._blocks += new_blocks


	def __str__(self):
		return self._name
		

class Villain(Agent):

	def __init__(self, name, forefather_hash):
		super(Villain, self).__init__(name)
		self._forefather_hash = forefather_hash
	
	def createTransaction(self, agent, time):
		if self._transactions == []:
			return

		transaction = random.choice(self._transactions)

		if transaction.hash == self._forefather_hash:
			return

		new_transaction = Transaction(
			parent=transaction,
			sender=transaction.remainder,
			recipient=TransactionElement(self, transaction.remainder.value * 0.5),
			remainder=TransactionElement(transaction.remainder.agent, 0),
			time=time
		)

		self._outcome_transactions.append(self._signature(new_transaction))

class Block(Entity):

	@property
	def age(self):
		if self.parent == None:
			return 0
		else:
			return self.parent.age + 1
	
	@property
	def parent(self):
		return self._parent

	@property
	def completed(self):
		return self._completed

	@property
	def transactions(self):
		return self._transactions

	@property
	def reward(self):
		return self._reward

	@property
	def owner(self):
		return self._owner

	@property
	def stime(self):
		return self._stime

	@property
	def etime(self):
		return self._etime
	
	@property
	def transactions_hashs(self):
		return [transaction.hash for transaction in self._transactions]
	
	def calculate(self, power, time):
		self._health -= 2 * power * random.random()

		if self._health <= 0:
			self._completed = True
			self._etime = time

	def __init__(self, owner, parent, transactions, time):
		super(Block, self).__init__()
		self._owner = owner
		self._completed = False
		self._parent = parent
		self._complexity = 1#network.generateComplexity()
		self._reward = 1#network.generateReward()
		self._health = 100 * self._complexity
		self._stime = time
		
		if(len(transactions) > 5):
			raise Exception('Попытка создать блок с неправильным количеством транзакций.')
		else:
			self._transactions = transactions

	def __str__(self):
		return "Block: " + str(len(self._transactions)) + ', ' + str(self.age)
		
class MinerAgent(Agent):

	def __init__(self, name, forefather_hash):
		super(MinerAgent, self).__init__(name)
		self._power = random.randint(25, 50)
		self._forefather_hash = forefather_hash
		self._currentBlock = None
	
	@property
	def known_transaction(self):
		return self.blocks_transactions_hashs + self.transactions_hashs

	@property
	def blocks_transactions_hashs(self):
		hashs = []
		for block in self.blocks:
			hashs += block.transactions_hashs
		return hashs

	@property
	def transactions_hashs(self):
		return list(map(lambda t: t.hash, self._transactions))
	
	def checkTransactionParents(self, transaction, generation=[]):

		if not transaction.hash in self.known_transaction:
			return False, generation

		if transaction.hash == self._forefather_hash:
			return True, generation

		if transaction.hash in self.blocks_transactions_hashs:
			return True, generation

		return self.checkTransactionParents(transaction.parent, generation + [transaction])

	@property
	def last_block(self):
		return sorted(self.blocks, key=lambda b: b.age, reverse=True)[0]

	def createBlock(self, time):
		
		verify_transactions = []
		work_transactions = []

		for transaction in self._transactions:
			if self.verify(transaction):
				verify_transactions.append(transaction)

		verify_transactions = sorted(verify_transactions, key=lambda t: t.reward)
		
		while verify_transactions != [] and len(work_transactions) < 5:
			transaction = verify_transactions.pop()
			can_add_transaction, generation = self.checkTransactionParents(transaction)
			if can_add_transaction:
				if len(generation) + len(work_transactions) <= 5:
					work_transactions += generation

		if work_transactions != []:
			if self._blocks == []:
				self._currentBlock = Block(self, None, work_transactions, time)
			else:
				self._currentBlock = Block(self, self.last_block, work_transactions, time)

	def mining(self, time):

		if self._currentBlock is None:
			self.createBlock(time)

		if self._currentBlock is None:
			return

		if self._currentBlock.parent != None:
			if self._currentBlock.parent.hash != self.last_block.hash:
				self._currentBlock = None
				self.mining(time)

		if not self._currentBlock.completed:
			self._currentBlock.calculate(self._power, time)

		if self._currentBlock.completed:
			self._blocks.append(self._currentBlock)
			self._currentBlock = None


	def verify(self, transaction):
		if transaction.hash == self._forefather_hash:
			return True
		try:
			pkcs1_15.new(transaction.sender.agent.pkey).verify(transaction.crypto_hash, transaction.signature)
		except ValueError as e:
			return False
		else:
			return True
		

		
class VillainMinerAgent(MinerAgent):

	def doEvil(self):
		print('Я делаю что-то плохое')
		