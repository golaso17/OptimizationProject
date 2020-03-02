import pandas as pd
from gurobipy import *
import numpy as np
import matplotlib.pyplot as plt

#SET flag if the arc data should be biderictional
biderictional = True

#Read data from files

demandData = pd.read_csv("DS9_Network_Node_Data.csv", header = 0, index_col = 0)

nodes = demandData.index.tolist()
demands = demandData.to_dict()['Demand']
group = demandData.to_dict()['Resident Group Number']

N = len(nodes) + 1
Ngroups = 0
for i in nodes:
    if group[i]>Ngroups:
        Ngroups = group[i]
# Assumes groups are numbered with consecutive integers starting from 1
print('Number of groups is ', Ngroups)
groupdemand = []
groupsat = []   #Demand satisfied in solution

for g in range(Ngroups):
    groupdemand.append(0)
    groupsat.append(0)
    

for i in nodes:
    groupdemand[group[i]-1] += demands[i]   #Indices start from 0 not 1
print("Total demand by group: ", groupdemand)

arcData = pd.read_csv("DS9_Network_Arc_Data.csv", header = 0)
arcs, capacity = multidict({(row[0] , row[1]) : row[2] for (index, row) in arcData.iterrows()})

#Rudimentary data processing to transform into a max flow network


if biderictional:
    for (i,j) in arcs:
        capacity.update({(j, i) : capacity[i,j]})

        

source = 0
sink = N

capacity.update({(source, 1): sum(demands.values())})

for node, demand in demands.items():
    capacity.update({(node, sink) : demand})



arcs, capacity = multidict(capacity)

#Max flow model. Can add another formulation.

m = Model('netflow')

# Create variables
flow = m.addVars(arcs, name="flow")
z = m.addVar(name="z")

#Set objective
m.setObjective(z, GRB.MAXIMIZE)

# Arc capacity constraints
m.addConstrs(
    (flow[i,j] <= capacity[i,j] for i,j in arcs), "cap")

# Flow conservation constraints
m.addConstrs(
    (flow.sum('*',j) == flow.sum(j,'*') for j in nodes), "node")

#FAIRNESS METRIC CONSTRAINT HERE
all_sols = []
for g in range(1,Ngroups+1):
    all_sols += [np.sum([flow[i,sink] for i in nodes if group[i] == g])]
all_sols = all_sols/np.array(groupdemand)
for expr in all_sols:
    m.addConstr(z<=expr)

# 95% constraint
m.addConstr(flow.sum('*',sink)>=.95*103)

# Compute optimal solution
m.write("project.lp")
m.optimize()

# Print solution
if m.status == GRB.Status.OPTIMAL:
    solution = m.getAttr('x', flow)
        
    for i,j in arcs:
        if solution[i,j] > 0:
            if j < N and j > 0:
                print('%s -> %s: %g' % (i, j, solution[i,j]))

    for i in nodes:
        if (i, sink) in arcs and demands[i] > 0 and demands[i]>solution[i,j]:
            print("Node %s recieved %g out of %g demanded: shortfall %g" % (i, solution[i,j], demands[i],demands[i]-solution[i,j]) )
        elif (i, sink) in arcs and demands[i] > 0:
            print("Node %s recieved %g out of %g demanded" % (i, solution[i,j], demands[i]) )
        groupsat[group[i]-1] += solution[i,sink]
    
    metric_min = []
    for g in range(Ngroups):
        if groupdemand[g] > 0:
            print("Group %s had proportion %g of its demand satisfied" % (g+1, groupsat[g]/groupdemand[g]))
            metric_min.append(groupsat[g]/groupdemand[g])
            
            
