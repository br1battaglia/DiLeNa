import requests
import multiprocessing as mp
import datetime
import sys
import time
from collections import Counter
import networkx
import json
import os



################################# CLASSES AND METHODS #####################################


class Transaction:
	def __init__(self, num, sender, receiver, amount):
		self.num = num
		self.sender = sender
		self.receiver = receiver
		self.amount = amount



#Find index of the first block
def findFirstBlock (timeBound, index):
	step = 10000
	descending = True
	while step > 0 or time < timeBound:   #finding the index of the blocks immediately before the lower bound and then returning index+1
		time = datetime.datetime.fromtimestamp(requests.get('https://sochain.com/api/v2/get_block/'+blockchain+'/'+str(index)).json()['data']['time']).strftime('%Y-%m-%d %H:%M:%S')
		if time < timeBound:
			index = index + step 
			if descending == True:
				step = int(step/2)   
				descending = False
		else: #time >, to decrease
			index = index - step
			if descending ==False:
				step = int(step/2)
				descending = True

	return index + 1

#find index of the last block
def findLastBlock (timeBound, index):
	step = 10000
	time = ''
	while step > 0:
		#print (str(time) + " ___" + str(timeBound) + "    " + str(step))
		response = requests.get('https://sochain.com/api/v2/get_block/'+blockchain+'/'+ str(index + step))
		exceed = False
		if response == '<Response [404]>':
			exceed = True
		else:
			time = datetime.datetime.fromtimestamp(response.json()['data']['time']).strftime('%Y-%m-%d %H:%M:%S')
			exceed = time > timeBound

		if exceed:
			step = int(step/2)
		else:
			index = index + step

	return index

#share the workload
def splitInterval (start, end, batches):
	each = int((end - start + 1) / batches)
	res = []
	iterator = start
	for i in range (batches):
		res.append([iterator, (iterator + each - 1)])
		iterator += each
	res [-1][1] = end
	return res


def download(intervals):
	lowerB = intervals[0] 
	upperB = intervals[1]
	blockIterator = lowerB
	multiInTx = []
	multiOutTx = []
	inAddress = [] 
	outAddress= []
	while blockIterator <= upperB:
		r = requests.get('https://sochain.com/api/v2/get_block/'+blockchain+'/'+ str(blockIterator)).json()
		print (datetime.datetime.fromtimestamp(r['data']['time']).strftime('%Y-%m-%d %H:%M:%S') + '   PID: '+str(+mp.current_process().pid))
		for y,t in enumerate(r['data']['txs']):
			tx = requests.get('https://sochain.com/api/v2/get_tx/'+blockchain+'/' + t)
			#need to clear the list every time there is a new transaction 
			inAddress.clear()
			outAddress.clear()
			try:
				tx = tx.json()
				for y,i in enumerate(tx['data']['inputs']):
					inputLenght = len(tx['data']['inputs'])
					nodeSet.add(i['address'])
					#the if statement is only for blockchains with multi-input transaction allowed
					if inputLenght > 1:
						counter = Counter(i['address'].split())
						#check if the multi input transaction has only one address repeated for every input address
						sameAddress = [i for i, j in counter.items() if j == inputLenght]
						#remove duplicate input address in the same multi input transaction
						if len(sameAddress) == 0:
							if i['address'] not in inAddress: 
								inAddress.append(i['address']) 
								#wa can append address only when for cycle ends. That's because we have to store all the addresses
								# of the multi input transaction
							if (y+1) == inputLenght:
								multiInTx.append(inAddress[:])
					for k,o in enumerate(tx['data']['outputs']):
						outputLenght = len(tx['data']['outputs'])
						nodeSet.add(o['address'])
						transList.append (Transaction(y,i['address'], o['address'], 0))  #amount currently disabled
						#coinbase transactions are not useful to cluster addresses
						if inputLenght == 1 and outputLenght > 1 and i['address'] != 'coinbase':
							if(k == 0):
								outAddress.append(tx['data']['time'])
								outAddress.append(i['address'])
								#we don't need transactions with self-change address for the change address heuristic
							if o['address'] == i['address']:
								outAddress.clear()
							else:
								outAddress.append(o['address'])
								if(k+1 == outputLenght):
									multiOutTx.append(outAddress[:])
			except Exception as inst:
				print (inst)
				time.sleep(cores * 5)
		blockIterator += 1
	return nodeSet, transList, multiInTx, multiOutTx



def to_edges(node):
    it = iter(node)
    last = next(it)
    for current in it:
        yield last, current
        last = current

def multiInputHeuristic(node):
    G = networkx.Graph()
    for part in node:
        # each sublist is a bunch of nodes
        G.add_nodes_from(part)
        # it also implies a number of edges:
        G.add_edges_from(to_edges(part))
    return G



"""
H2 
An output oj(t) is the change address if these four conditions are met:
1. This is the first appearance of the address oj(t).
2. The transaction t is not a coin generation transaction.
3. There is no address within the outputs, which also appears on the input side (self-change address).
4. Condition 1 is only met for exactly one oj(t) and not also for some ok(t) with j ≠ k 

H2c: we demand that the address also does not occur in later transactions (except for one occurrence as an input)
"""

def changeAddressHeuristic(node):
	changeTransaction = False
	address = []
	cluster = []
	for i in range(len(node)):
		date = node[i][0]
		address.append(node[i][1])
		for j in range(1, len(node[i])):
			outputNode = node[i][j]
			tx = requests.get('https://sochain.com/api/v2/address/'+blockchain+'/' + outputNode).json()
			#we check if the first transaction ever of the node is equals to the date of the transaction we are considering
			#if false, the node can't be a change address because it must be a fresh node
			#H2
			""" if tx['data']['txs'][-1]['time'] == date and tx['data']['total_txs'] == 1 and changeTransaction == False:
					address.append(outputNode)
					changeTransaction = True """
			#H2c 
			if tx['data']['txs'][-1]['time'] == date and tx['data']['total_txs'] == 2 and changeTransaction == False and 'outgoing' in tx['data']['txs'][0]:
				address.append(outputNode)
				changeTransaction = True
			if tx['data']['txs'][-1]['time'] == date and tx['data']['total_txs'] == 2 and changeTransaction == True:
				address.clear()
				break
			if changeTransaction == True and j+1 == len(node[i]):
				cluster.append(address)
	return cluster

				
			
			
		



#################################### Main ##################################################

transList=[]
multiInputTx = []
multiOutputTx = []
nodeSet = set()
nodeDict={}
cluster = []
cores = 1

if len(sys.argv) > 3:
	blockchain = (sys.argv[1]).upper()
	start = list(sys.argv[2])
	start[10] = ' '             #adding ' ' between date and hour as requested by the API
	start = "".join(start)
	end = list(sys.argv[3])
	end[10] = ' '
	end = "".join(end)
	if len(sys.argv) > 4:
		fileRes = sys.argv[4]
	else:
		if blockchain == 'LTC':
			fileRes = "res/litecoin.net" 
		elif blockchain == 'DOGE':
			fileRes = "res/doge.net" 
		elif blockchain == 'BTC':
			fileRes = "res/bitcoin.net" 
	if len(sys.argv) == 6:
		cores = int(sys.argv[5])
pool = mp.Pool(processes=cores) 

print ("Finding the index of the first block")
if blockchain == 'LTC':
	firstBlock = findFirstBlock(start, 2007468) #last block at 27/02/2021 12:00
elif blockchain == 'DOGE':
	firstBlock = findFirstBlock(start, 3623758) #last block at 27/02/2021 12:00
elif  blockchain == 'BTC':
	firstBlock = findFirstBlock(start, 672263)	#last block at 27/02/2021 13:09
print ("Finding the index of the last block")
lastBlock = findLastBlock (end, firstBlock)
print("Start reading the blocks")
dates_pairs = splitInterval (firstBlock, lastBlock, cores)

parallelRes = pool.map(download, dates_pairs)
pool.close()
for batch in parallelRes:
	for item in batch[0]:
		nodeSet.add(item)
	for item in batch[1]:
		transList.append(item)
	for item in batch[2]:
		multiInputTx.append(item)
	for item in batch[3]:
		#the first argoument is the date and the second one is the input address
		multiOutputTx.append(item)

clusterH1 = multiInputHeuristic(multiInputTx)
clusterH2 = changeAddressHeuristic(multiOutputTx)


os.makedirs(os.path.dirname(fileRes), exist_ok=True)
with open(fileRes, 'w') as f:	
	print ("Saving the graph in " + fileRes)	
	print ('*Vertices ' + str(len(nodeSet)), file=f)
	for elem in enumerate (nodeSet):
		nodeDict[elem[1]] = elem[0]
		print (str(elem[0]) + ' "' + str(elem[1]) + '"', file = f)

	print("\n", file = f)	

	print ("*Arcs " + str(len(transList)), file = f)
	for t in transList:		
		print(str(nodeDict[t.sender]) + ' ' +  str(nodeDict[t.receiver]) + ' ' + str(t.amount), file = f)

	print("\n", file = f)

	print ("Address in multi input transactions: " + str(len(multiInputTx)), file = f)
	for tx in multiInputTx:			
		print(tx, file = f)

	print("\n", file = f)
	
	print ("Address in multi output transactions: " + str(len(multiOutputTx)), file = f)
	for tx in multiOutputTx:			
		print(tx, file = f)

	print("\n", file = f)

	print ("Cluster: "+str(len(clusterH1)), file = f)
	for cl in clusterH1:
		print(cl, file =f)